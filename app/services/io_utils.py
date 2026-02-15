# archivo: app/services/io_utils.py

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ParsedData:
    x: np.ndarray
    y: np.ndarray
    columns_used: Tuple[str, str]


def _norm(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _find_columns(df: pd.DataFrame) -> Tuple[str, str]:
    cols = list(df.columns)
    norm_map = {_norm(c): c for c in cols}

    pressure_keys = [
        "p [bar]",
        "p[bar]",
        "p (bar)",
        "p(bar)",
        "pressure [bar]",
        "pressure(bar)",
        "pressure",
        "presion [bar]",
        "presión [bar]",
        "presion(bar)",
        "presión(bar)",
        "p",
        "presion",
        "presión",
    ]
    uptake_keys = [
        "mmol/g co2",
        "mmol/gco2",
        "mmol g-1 co2",
        "mmol/g",
        "uptake",
        "adsorption",
        "loading",
        "q",
        "q co2",
        "co2 uptake",
    ]

    p_col = None
    y_col = None

    for k in pressure_keys:
        if k in norm_map:
            p_col = norm_map[k]
            break
    for k in uptake_keys:
        if k in norm_map:
            y_col = norm_map[k]
            break

    # Fallback heurístico
    if p_col is None:
        for nk, orig in norm_map.items():
            if "bar" in nk and (
                re.search(r"\bp\b", nk)
                or "pressure" in nk
                or "presion" in nk
                or "presión" in nk
            ):
                p_col = orig
                break

    if y_col is None:
        for nk, orig in norm_map.items():
            if ("mmol" in nk and "co2" in nk) or (nk == "q"):
                y_col = orig
                break

    if p_col is None or y_col is None:
        raise ValueError(
            "No se encontraron columnas requeridas. "
            "Se esperan 'P [bar]' y 'mmol/g co2' (o variantes similares)."
        )

    return p_col, y_col


def _clean_xy(df: pd.DataFrame, p_col: str, y_col: str) -> ParsedData:
    df2 = df[[p_col, y_col]].copy()
    df2[p_col] = pd.to_numeric(df2[p_col], errors="coerce")
    df2[y_col] = pd.to_numeric(df2[y_col], errors="coerce")
    df2 = df2.dropna()

    if df2.empty:
        raise ValueError(
            "No hay datos numéricos válidos tras limpiar NaN/no-numéricos."
        )

    df2 = df2.sort_values(p_col)
    df2 = df2.groupby(p_col, as_index=False)[y_col].mean()

    x = df2[p_col].to_numpy(dtype=float)
    y = df2[y_col].to_numpy(dtype=float)

    if len(x) < 3:
        raise ValueError("Se requieren al menos 3 puntos (presiones únicas).")

    return ParsedData(x=x, y=y, columns_used=(p_col, y_col))


def parse_uploaded_file(filename: str, content: bytes) -> ParsedData:
    name = filename.lower().strip()
    buf = io.BytesIO(content)

    if name.endswith(".csv"):
        df = pd.read_csv(buf)
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(buf)
    else:
        raise ValueError("Formato no soportado. Usa .csv o .xlsx/.xls")

    p_col, y_col = _find_columns(df)
    return _clean_xy(df, p_col, y_col)


def parse_manual_points(points: list[dict]) -> ParsedData:
    """
    points: [{"p": <bar>, "q": <mmol/g>}, ...]
    """
    if not isinstance(points, list) or len(points) < 3:
        raise ValueError("Para modo manual se requieren al menos 3 puntos.")

    df = pd.DataFrame(points)

    if "p" not in df.columns or "q" not in df.columns:
        raise ValueError("Formato manual inválido: cada punto debe tener 'p' y 'q'.")

    df["p"] = pd.to_numeric(df["p"], errors="coerce")
    df["q"] = pd.to_numeric(df["q"], errors="coerce")
    df = df.dropna()

    if df.empty or len(df) < 3:
        raise ValueError("Puntos manuales inválidos o insuficientes (mínimo 3).")

    df = df.sort_values("p")
    df = df.groupby("p", as_index=False)["q"].mean()

    if len(df) < 3:
        raise ValueError("Se requieren al menos 3 presiones únicas en puntos manuales.")

    return ParsedData(
        x=df["p"].to_numpy(dtype=float),
        y=df["q"].to_numpy(dtype=float),
        columns_used=("P [bar]", "mmol/g co2"),
    )


def merge_datasets(
    file_data: Optional[ParsedData], manual_data: Optional[ParsedData]
) -> ParsedData:
    if file_data is None and manual_data is None:
        raise ValueError("No hay datos. Sube un archivo o ingresa puntos manuales.")

    if file_data is None:
        return manual_data
    if manual_data is None:
        return file_data

    df = pd.DataFrame(
        {
            "P [bar]": np.concatenate([file_data.x, manual_data.x]),
            "mmol/g co2": np.concatenate([file_data.y, manual_data.y]),
        }
    )

    df = df.dropna().sort_values("P [bar]")
    df = df.groupby("P [bar]", as_index=False)["mmol/g co2"].mean()

    if len(df) < 3:
        raise ValueError("Tras combinar, se requieren al menos 3 presiones únicas.")

    return ParsedData(
        x=df["P [bar]"].to_numpy(dtype=float),
        y=df["mmol/g co2"].to_numpy(dtype=float),
        columns_used=("P [bar]", "mmol/g co2"),
    )
