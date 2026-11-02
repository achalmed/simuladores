"""studio/sim_app/servicios/corridas.py — correr un escenario y preparar lo que la ventana dibuja (sin Qt).

`correr` llama a `navegador.calcular` (lo mismo que ejecuta el navegador de los pubs): los valores pedidos ajustados al
rango de cada parámetro, las curvas serializadas y los resultados. `para_grafico` convierte las curvas al contrato de
`GuiComun.Grafico`: QuickCharts posiciona cada valor por su índice, así que las líneas se remuestrean sobre una rejilla
común de x (interpolación lineal) y una línea con x o y constante pasa a ser una marca. `comparar` enfrenta las
magnitudes del escenario con las de la base. `csv_series` y `json_corrida` son lo que se exporta."""
from __future__ import annotations

import csv
import io
import json
import math
import re

PUNTOS_REJILLA = 200
ETIQUETAS_EJE = 5


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


def _interpolar(xs: list[float], ys: list[float], rejilla: list[float]) -> list[float]:
    """Interpolación lineal de (xs, ys) sobre la rejilla; fuera del dominio de la serie repite el borde."""
    pares = sorted((x, y) for x, y in zip(xs, ys) if x is not None and y is not None)
    if not pares:
        return [0.0] * len(rejilla)
    salida = []
    j = 0
    for x in rejilla:
        while j + 1 < len(pares) and pares[j + 1][0] <= x:
            j += 1
        x0, y0 = pares[j]
        if j + 1 < len(pares) and pares[j + 1][0] > x0 and x > x0:
            x1, y1 = pares[j + 1]
            salida.append(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
        else:
            salida.append(y0)
    return salida


def para_grafico(curvas: dict, xlabel: str = "", ylabel: str = "", puntos_rejilla: int = PUNTOS_REJILLA) -> dict:
    """Las propiedades de `GuiComun.Grafico` a partir de las curvas serializadas (`navegador.serializar`)."""
    salida = {"series": [], "etiquetasX": [], "xMinimo": 0.0, "xMaximo": 1.0, "yMinimo": 0.0, "yMaximo": 1.0,
              "barras": {}, "puntos": [], "equilibrio": None, "marcas": [], "etiquetaX": sin_mathtext(xlabel),
              "etiquetaY": sin_mathtext(ylabel), "anotacion": sin_mathtext(curvas.get("anotacion", "")).replace("\\n", " · ")}
    ys_todas: list[float] = []
    barras = curvas.get("barras")
    if barras:
        valores = [_numero(v) or 0.0 for v in barras.get("valores", [])]
        salida["barras"] = {"categorias": [sin_mathtext(c) for c in barras.get("categorias", [])], "valores": valores}
        ys_todas += valores + [0.0]
        salida["etiquetaX"] = ""
    lineas, marcas = [], []
    for linea in curvas.get("lineas") or []:
        xs = [_numero(v) for v in linea.get("x", [])]
        ys = [_numero(v) for v in linea.get("y", [])]
        validos = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
        if not validos:
            continue
        xv, yv = [p[0] for p in validos], [p[1] for p in validos]
        nombre = sin_mathtext(linea.get("etiqueta", ""))
        if max(xv) - min(xv) < 1e-12:                       # x constante: una línea vertical
            marcas.append({"x": xv[0], "etiqueta": nombre})
            ys_todas += yv
            continue
        if max(yv) - min(yv) < 1e-12 and len(yv) > 1:       # y constante: una línea horizontal
            marcas.append({"y": yv[0], "etiqueta": nombre})
            ys_todas += yv
            lineas.append((nombre, xv, yv, True))
            continue
        lineas.append((nombre, xv, yv, False))
        ys_todas += yv
    xs_lineas = [x for _n, xv, _y, _h in lineas for x in (min(xv), max(xv))] + [m["x"] for m in marcas if "x" in m]
    for p in curvas.get("puntos") or []:
        x, y = _numero(p.get("x")), _numero(p.get("y"))
        if x is not None and y is not None:
            salida["puntos"].append({"x": x, "y": y, "etiqueta": sin_mathtext(p.get("etiqueta", ""))})
            xs_lineas.append(x)
            ys_todas.append(y)
    eq = curvas.get("equilibrio")
    if eq and _numero(eq.get("x")) is not None and _numero(eq.get("y")) is not None:
        salida["equilibrio"] = {"x": float(eq["x"]), "y": float(eq["y"]), "etiqueta": "E"}
        xs_lineas.append(float(eq["x"]))
        ys_todas.append(float(eq["y"]))
    if xs_lineas:
        x0, x1 = min(xs_lineas), max(xs_lineas)
        if x1 - x0 < 1e-12:
            x0, x1 = x0 - 1, x1 + 1
        rejilla = [x0 + i * (x1 - x0) / (puntos_rejilla - 1) for i in range(puntos_rejilla)]
        salida["series"] = [{"nombre": n, "y": _interpolar(xv, yv, rejilla)} for n, xv, yv, horizontal in lineas if not horizontal]
        salida["xMinimo"], salida["xMaximo"] = x0, x1
        salida["etiquetasX"] = [_etiqueta_numero(x0 + i * (x1 - x0) / (ETIQUETAS_EJE - 1)) for i in range(ETIQUETAS_EJE)]
    if ys_todas:
        y0, y1 = min(ys_todas), max(ys_todas)
        if y1 - y0 < 1e-12:
            y0, y1 = y0 - 1, y1 + 1
        margen = (y1 - y0) * 0.05
        salida["yMinimo"], salida["yMaximo"] = (0.0 if barras and y0 >= 0 else y0 - margen), y1 + margen
    salida["marcas"] = marcas
    return salida


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
