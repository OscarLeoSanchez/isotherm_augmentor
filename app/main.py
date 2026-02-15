# archivo: app/main.py

from __future__ import annotations

import io
import json
from typing import Optional, Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.io_utils import (
    parse_uploaded_file,
    parse_manual_points,
    merge_datasets,
    ParsedData,
)
from app.services.methods import compute_all_methods


app = FastAPI(title="Isotherm Augmentor", version="3.0.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Página de pruebas para verificar funcionalidad de la API"""
    from pathlib import Path
    test_file = Path(__file__).parent.parent / "test.html"
    if test_file.exists():
        return HTMLResponse(content=test_file.read_text(encoding="utf-8"))
    return HTMLResponse("Test page not found", status_code=404)


@app.post("/api/compute")
async def api_compute(
    file: Optional[UploadFile] = File(default=None),
    manual_points_json: str = Form(default="[]"),
    n_points: int = Form(default=200),
    smoothing_s: float = Form(default=0.0),
    poly_degree: int = Form(default=3),
):
    # Parse manual json
    try:
        manual_points = json.loads(manual_points_json) if manual_points_json else []
        if not isinstance(manual_points, list):
            raise ValueError("manual_points_json debe ser una lista.")
    except Exception:
        raise HTTPException(
            status_code=400, detail="manual_points_json inválido (debe ser JSON lista)."
        )

    data_file: Optional[ParsedData] = None
    data_manual: Optional[ParsedData] = None

    # File optional
    if file is not None:
        try:
            content = await file.read()
            data_file = parse_uploaded_file(file.filename, content)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error leyendo archivo: {str(e)}"
            )

    # Manual optional
    if manual_points and len(manual_points) > 0:
        # Si el usuario puso algo manual, exigimos consistencia mínima (>=3)
        try:
            data_manual = parse_manual_points(manual_points)
        except Exception as e:
            # Si NO hay archivo, este error debe verse claro
            if data_file is None:
                raise HTTPException(status_code=400, detail=str(e))
            # Si hay archivo, dejamos que el cálculo siga solo con archivo
            data_manual = None

    if data_file is None and data_manual is None:
        raise HTTPException(
            status_code=400,
            detail="Sube un archivo o ingresa al menos 3 puntos manuales.",
        )

    # Merge
    try:
        parsed = merge_datasets(data_file, data_manual)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error combinando datos: {str(e)}")

    # Compute
    try:
        out = compute_all_methods(
            parsed.x,
            parsed.y,
            n_points=n_points,
            smoothing_s=smoothing_s,
            poly_degree=poly_degree,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    x_grid = out["x_grid"]
    results = out["results"]
    method_order = out["method_order"]

    payload = {
        "original": {
            "x": parsed.x.tolist(),
            "y": parsed.y.tolist(),
            "n_original": int(len(parsed.x)),
            "columns_used": list(parsed.columns_used),
        },
        "grid": x_grid.tolist(),
        "methods": {
            k: {"y": v.y_pred.tolist(), "meta": v.meta} for k, v in results.items()
        },
        "method_order": method_order,
        "labels": {"x": "P [bar]", "y": "mmol/g co2"},
    }
    return JSONResponse(payload)


@app.post("/api/export")
async def api_export(
    export_format: Literal["csv", "xlsx"] = Form(...),
    selected_methods_json: str = Form(...),
    grid_json: str = Form(...),
    results_json: str = Form(...),
):
    """
    selected_methods_json: ["pchip","gpr",...]
    grid_json: [x1,x2,...]
    results_json: {"pchip":[y..], "gpr":[y..], ...}
    """
    try:
        selected = json.loads(selected_methods_json)
        x = np.array(json.loads(grid_json), dtype=float)
        results = json.loads(results_json)

        if not isinstance(selected, list) or len(selected) == 0:
            raise ValueError("Selecciona al menos un método.")
        if x.ndim != 1:
            raise ValueError("Grid inválido.")
        for m in selected:
            if m not in results:
                raise ValueError(f"Método faltante en results: {m}")
            y = np.array(results[m], dtype=float)
            if y.shape != x.shape:
                raise ValueError(f"Dimensiones no coinciden para {m}.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if export_format == "csv":
        # Formato largo: method,P [bar],mmol/g co2
        rows = []
        for m in selected:
            for xi, yi in zip(x.tolist(), results[m]):
                rows.append({"method": m, "P [bar]": xi, "mmol/g co2": float(yi)})
        df = pd.DataFrame(rows)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        data = buf.getvalue().encode("utf-8")
        return StreamingResponse(
            io.BytesIO(data),
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="export_selected_methods.csv"'
            },
        )

    # XLSX con hoja por método
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for m in selected:
            df = pd.DataFrame(
                {"P [bar]": x, "mmol/g co2": np.array(results[m], dtype=float)}
            )
            sheet = m[:31]  # límite Excel
            df.to_excel(writer, index=False, sheet_name=sheet)
    out.seek(0)
    return StreamingResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="export_selected_methods.xlsx"'
        },
    )
