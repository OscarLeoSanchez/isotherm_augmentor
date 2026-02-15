# archivo: app/services/methods.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Tuple

import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator, UnivariateSpline


@dataclass(frozen=True)
class MethodResult:
    y_pred: np.ndarray
    meta: Dict[str, Any]


def _prepare_xy(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    order = np.argsort(x)
    x = x[order]
    y = y[order]

    ux, inv = np.unique(x, return_inverse=True)
    if len(ux) != len(x):
        y_acc = np.zeros_like(ux, dtype=float)
        cnt = np.zeros_like(ux, dtype=float)
        for i, j in enumerate(inv):
            y_acc[j] += y[i]
            cnt[j] += 1
        x = ux
        y = y_acc / np.maximum(cnt, 1)

    if len(x) < 3:
        raise ValueError("Se requieren al menos 3 puntos (presiones únicas).")

    return x, y


def _grid(x: np.ndarray, n_points: int) -> np.ndarray:
    n_points = int(n_points)
    if n_points < 3:
        raise ValueError("n_points debe ser >= 3.")
    return np.linspace(float(np.min(x)), float(np.max(x)), n_points)


def compute_all_methods(
    x: np.ndarray,
    y: np.ndarray,
    n_points: int,
    smoothing_s: float = 0.0,
    poly_degree: int = 3,
) -> dict:
    x, y = _prepare_xy(x, y)
    xg = _grid(x, n_points)

    results: dict[str, MethodResult] = {}

    # 1) Linear
    results["linear"] = MethodResult(
        y_pred=np.interp(xg, x, y),
        meta={"name": "Linear", "family": "interpolation"},
    )

    # 2) CubicSpline (natural)
    cs = CubicSpline(x, y, bc_type="natural")
    results["cubic_spline"] = MethodResult(
        y_pred=cs(xg),
        meta={"name": "CubicSpline", "family": "spline"},
    )

    # 3) PCHIP (shape-preserving)
    pchip = PchipInterpolator(x, y)
    results["pchip"] = MethodResult(
        y_pred=pchip(xg),
        meta={"name": "PCHIP", "family": "interpolation"},
    )

    # 4) Smoothing spline
    s = float(smoothing_s)
    if s < 0:
        raise ValueError("smoothing_s debe ser >= 0.")
    us = UnivariateSpline(x, y, s=s)
    results["smoothing_spline"] = MethodResult(
        y_pred=us(xg),
        meta={"name": "Smoothing Spline", "family": "spline", "s": s},
    )

    # 5) Polynomial regression
    deg = int(poly_degree)
    if deg < 1 or deg > 10:
        raise ValueError("poly_degree debe estar entre 1 y 10.")
    coeffs = np.polyfit(x, y, deg=deg)
    poly = np.poly1d(coeffs)
    results["poly"] = MethodResult(
        y_pred=poly(xg),
        meta={"name": f"Polynomial (deg={deg})", "family": "regression", "degree": deg},
    )

    return {
        "x_grid": xg,
        "results": results,
        "method_order": [
            "pchip",
            "smoothing_spline",
            "cubic_spline",
            "linear",
            "poly",
        ],
    }
