"""studio/sim_app/servicios/corridas.py — correr un escenario y preparar lo que la ventana dibuja (sin Qt).

`correr` llama a `navegador.calcular` (lo mismo que ejecuta el navegador de los pubs): los valores pedidos ajustados al
rango de cada parámetro, las curvas serializadas y los resultados. `comparar` enfrenta las magnitudes del escenario con
las de la base. `csv_series` y `json_corrida` son lo que se exporta. Lo que el gráfico dibuja lo prepara
`servicios.simulacion` (cada línea con su x real; la reingeniería retiró el remuestreo para QuickCharts)."""
from __future__ import annotations

import csv
import io
import json
import math
import re



def correr(navegador, modelo, valores: dict | None) -> dict:
    """{valores, curvas, resultados} del modelo con los valores pedidos (navegador.calcular)."""
    return navegador.calcular(modelo, valores or {})


def sin_mathtext(texto: str) -> str:
    """Una etiqueta de matplotlib («Producto ($Y$)», «$\\bar X$») legible en un control de texto."""
    t = str(texto or "")
    t = re.sub(r"\\(bar|hat|tilde|mathrm|mathbf|text)\{([^{}]*)\}", r"\2", t)
    t = re.sub(r"\\(bar|hat|tilde)\s*([A-Za-z])", r"\2", t)
    t = re.sub(r"\\(alpha|beta|gamma|delta|sigma|mu|pi|lambda|theta|rho|epsilon|phi|omega)", lambda m: {
        "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "sigma": "σ", "mu": "μ", "pi": "π", "lambda": "λ",
        "theta": "θ", "rho": "ρ", "epsilon": "ε", "phi": "φ", "omega": "ω"}[m.group(1)], t)
    t = re.sub(r"\^\{?\*\}?", "*", t)
    t = t.replace("$", "").replace("\\,", " ").replace("\\;", " ").replace("\\ ", " ").replace("{", "").replace("}", "")
    t = re.sub(r"\\([a-zA-Z]+)", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()


def _numero(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _etiqueta_numero(v: float) -> str:
    a = abs(v)
    if a >= 1000:
        texto = f"{v:,.0f}"
    elif a >= 10:
        texto = f"{v:,.1f}"
    elif a >= 1:
        texto = f"{v:.2f}"
    else:
        texto = f"{v:.3g}"
    return texto.replace(",", " ")


def comparar(base: list, escenario: list) -> list[dict]:
    """[{magnitud, base, escenario, delta, pct}] de las magnitudes numéricas (`navegador.resultados` devuelve [[k, v]])."""
    de_base = {k: v for k, v in base}
    filas = []
    for k, v1 in escenario:
        v0 = de_base.get(k)
        n0, n1 = _numero(v0), _numero(v1)
        if n0 is None or n1 is None:
            filas.append({"magnitud": str(k), "base": str(v0 if v0 is not None else "—"), "escenario": str(v1), "delta": "", "pct": "", "signo": ""})
            continue
        d = n1 - n0
        pct = f"{100 * d / abs(n0):+.1f} %" if abs(n0) > 1e-12 else "—"
        filas.append({"magnitud": str(k), "base": _etiqueta_numero(n0), "escenario": _etiqueta_numero(n1),
                      "delta": (f"{d:+,.4g}".replace(",", " ") if abs(d) > 1e-12 else "="), "pct": pct if abs(d) > 1e-12 else "=",
                      "signo": "↑" if d > 1e-12 else ("↓" if d < -1e-12 else "=")})
    return filas


def csv_series(curvas: dict) -> str:
    """Las series de la corrida en CSV: una columna x e y por línea (cada línea con su propio x), o las barras."""
    salida = io.StringIO()
    w = csv.writer(salida)
    barras = curvas.get("barras")
    if barras:
        w.writerow(["categoria", "valor"])
        for c, v in zip(barras.get("categorias", []), barras.get("valores", [])):
            w.writerow([c, v])
    lineas = curvas.get("lineas") or []
    if lineas:
        if barras:
            w.writerow([])
        w.writerow([f"{col}" for linea in lineas for col in (f"x · {linea.get('etiqueta', '')}", f"y · {linea.get('etiqueta', '')}")])
        largo = max(len(linea.get("x", [])) for linea in lineas)
        for i in range(largo):
            fila = []
            for linea in lineas:
                xs, ys = linea.get("x", []), linea.get("y", [])
                fila += [xs[i] if i < len(xs) else "", ys[i] if i < len(ys) else ""]
            w.writerow(fila)
    return salida.getvalue()


def json_corrida(corrida: dict, ref: str, escenario: str) -> str:
    return json.dumps({"ref": ref, "escenario": escenario, **corrida}, ensure_ascii=False, indent=1, allow_nan=False) + "\n"
