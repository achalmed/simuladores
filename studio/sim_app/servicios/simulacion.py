"""studio/sim_app/servicios/simulacion.py — lo que el espacio de simulación dibuja y decide (reingeniería L2–L8; sin Qt).

- `grafico(curvas, xlabel, ylabel)`: las curvas serializadas (`navegador.serializar`) para `GraficoCientifico.qml`: cada
  línea con su propio x (sin remuestrear: a lo sumo se ralea tomando uno de cada k puntos, conservando los extremos),
  las barras con el rol de color de cada una (`paleta`), los puntos, el equilibrio, las líneas verticales y horizontales
  y los límites de los ejes. `unir_limites` da la misma escala a dos gráficos (base y escenario lado a lado).
- `sensibilidad(base, modelo, parametro, magnitud, n)`: el barrido del parámetro sobre su rango con `base.sensibilidad`
  del motor, más robusto: cada punto que no calcula o no es finito queda marcado y fuera de la curva.
- `validez(estado, fallos, corrida)`: si una corrida puede presentarse como válida (L8).
- `es_temporal(xlabel)`: si el eje x es el tiempo (L7).
"""
from __future__ import annotations

import math
import re

from sim_app.servicios import paleta
from sim_app.servicios.corridas import sin_mathtext

MAX_PUNTOS = 600
_TIEMPO = re.compile(r"(^|[^a-záéíóú])(t|tiempo|periodo|período|periodos|años?|trimestres?|meses|mes|semanas?|días?|generaci[oó]n(es)?|iteraci[oó]n(es)?|ronda)([^a-záéíóú]|$)",
                     re.IGNORECASE)


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _ralear(xs: list, ys: list, tope: int = MAX_PUNTOS) -> tuple[list, list]:
    if len(xs) <= tope:
        return xs, ys
    paso = math.ceil(len(xs) / tope)
    idx = list(range(0, len(xs), paso))
    if idx[-1] != len(xs) - 1:
        idx.append(len(xs) - 1)
    return [xs[i] for i in idx], [ys[i] for i in idx]


def es_temporal(xlabel: str) -> bool:
    """¿El eje x es el tiempo? (t, periodo, año, trimestre, mes, generación, iteración…)."""
    return bool(_TIEMPO.search(sin_mathtext(xlabel or "")))


def grafico(curvas: dict, xlabel: str = "", ylabel: str = "") -> dict:
    """Los datos de `GraficoCientifico` desde las curvas serializadas; `limites` con un margen."""
    salida = {"lineas": [], "barras": {}, "puntos": [], "equilibrio": None, "verticales": [], "horizontales": [],
              "etiquetaX": sin_mathtext(xlabel), "etiquetaY": sin_mathtext(ylabel), "temporal": es_temporal(xlabel),
              "anotacion": " · ".join(sin_mathtext(t) for t in str(curvas.get("anotacion", "")).replace("\\n", "\n").split("\n") if t.strip()),
              "noFinitos": 0}
    xs_todas, ys_todas = [], []
    for i, linea in enumerate(curvas.get("lineas") or []):
        pares = [(_num(x), _num(y)) for x, y in zip(linea.get("x", []), linea.get("y", []))]
        salida["noFinitos"] += sum(1 for x, y in pares if x is None or y is None)
        validos = [(x, y) for x, y in pares if x is not None and y is not None]
        if not validos:
            continue
        xv, yv = [p[0] for p in validos], [p[1] for p in validos]
        nombre = sin_mathtext(linea.get("etiqueta", ""))
        r = paleta.rol(linea.get("color", ""), i)
        if max(xv) - min(xv) < 1e-12:
            salida["verticales"].append({"x": xv[0], "nombre": nombre, "rol": r})
            ys_todas += yv
            xs_todas.append(xv[0])
            continue
        if max(yv) - min(yv) < 1e-12 and len(yv) > 1:
            salida["horizontales"].append({"y": yv[0], "nombre": nombre, "rol": r})
            ys_todas.append(yv[0])
            xs_todas += [min(xv), max(xv)]
            continue
        xv, yv = _ralear(xv, yv)
        salida["lineas"].append({"nombre": nombre, "x": xv, "y": yv, "rol": r})
        xs_todas += [min(xv), max(xv)]
        ys_todas += yv
    barras = curvas.get("barras")
    if barras:
        valores = [_num(v) for v in barras.get("valores", [])]
        salida["noFinitos"] += sum(1 for v in valores if v is None)
        valores = [v if v is not None else 0.0 for v in valores]
        salida["barras"] = {"categorias": [sin_mathtext(c) for c in barras.get("categorias", [])], "valores": valores,
                            "roles": paleta.roles(barras.get("colores", []) or [""] * len(valores))}
        ys_todas += valores + [0.0]
    for p in curvas.get("puntos") or []:
        x, y = _num(p.get("x")), _num(p.get("y"))
        if x is not None and y is not None:
            salida["puntos"].append({"x": x, "y": y, "nombre": sin_mathtext(p.get("etiqueta", ""))})
            xs_todas.append(x)
            ys_todas.append(y)
    eq = curvas.get("equilibrio")
    if eq and _num(eq.get("x")) is not None and _num(eq.get("y")) is not None:
        salida["equilibrio"] = {"x": float(eq["x"]), "y": float(eq["y"])}
        xs_todas.append(float(eq["x"]))
        ys_todas.append(float(eq["y"]))
    salida["limites"] = _limites(xs_todas, ys_todas, bool(barras))
    return salida


def _limites(xs: list, ys: list, con_barras: bool) -> dict:
    x0, x1 = (min(xs), max(xs)) if xs else (0.0, 1.0)
    y0, y1 = (min(ys), max(ys)) if ys else (0.0, 1.0)
    if x1 - x0 < 1e-12:
        x0, x1 = x0 - 1, x1 + 1
    if y1 - y0 < 1e-12:
        y0, y1 = y0 - 1, y1 + 1
    m = (y1 - y0) * 0.06
    return {"xMin": x0, "xMax": x1, "yMin": 0.0 if con_barras and y0 >= 0 else y0 - m, "yMax": y1 + m}


def unir_limites(*graficos: dict) -> dict:
    """Los límites que contienen a todos (la misma escala para comparar)."""
    ls = [g.get("limites") for g in graficos if g and g.get("limites")]
    if not ls:
        return {"xMin": 0.0, "xMax": 1.0, "yMin": 0.0, "yMax": 1.0}
    return {"xMin": min(l["xMin"] for l in ls), "xMax": max(l["xMax"] for l in ls),
            "yMin": min(l["yMin"] for l in ls), "yMax": max(l["yMax"] for l in ls)}


def magnitudes(resultados: list) -> list[str]:
    """Las magnitudes numéricas de `navegador.resultados` ([[nombre, valor]])."""
    return [str(k) for k, v in resultados if _num(v) is not None]


def sensibilidad(base, modelo, parametro: str, magnitud: str = "", n: int = 25) -> dict:
    """{parametro, etiqueta, magnitud, x, y, fallidos, actual, valorActual, derivada, unidad} sobre el rango declarado.

    La malla, el valor base y la derivada central los da `base.sensibilidad` del motor (n puntos); si el motor falla en
    algún punto del rango, se barre punto a punto y los puntos que no calculan quedan en `fallidos`."""
    p = modelo.parametro(parametro)
    try:
        r = base.sensibilidad(modelo, parametro, magnitud or None, n=n)
        xs, ys = [float(v) for v, _y in r["filas"]], [_num(y) for _v, y in r["filas"]]
        magnitud, derivada = r["magnitud"], _num(r["derivada"])
    except KeyError:
        raise
    except Exception:       # noqa: BLE001  un punto del rango fuera de dominio: punto a punto
        res = modelo.calcular()
        magnitud = magnitud or next(k for k, v in res.items() if isinstance(v, (int, float)))
        xs, ys = [], []
        for i in range(n):
            v = p.minimo + i * (p.maximo - p.minimo) / (n - 1)
            xs.append(v)
            try:
                ys.append(_num(modelo.calcular(**{parametro: v})[magnitud]))
            except Exception:       # noqa: BLE001
                ys.append(None)
        try:
            h = p.paso or (p.maximo - p.minimo) / 100
            derivada = _num((modelo.calcular(**{parametro: p.valor + h})[magnitud] - modelo.calcular(**{parametro: p.valor - h})[magnitud]) / (2 * h))
        except Exception:       # noqa: BLE001
            derivada = None
    try:
        actual = _num(modelo.calcular()[magnitud])
    except Exception:       # noqa: BLE001
        actual = None
    fallidos = [x for x, y in zip(xs, ys) if y is None]
    pares = [(x, y) for x, y in zip(xs, ys) if y is not None]
    etiqueta = p.etiqueta or p.nombre
    curvas = {"lineas": [{"etiqueta": magnitud, "x": [a for a, _b in pares], "y": [b for _a, b in pares], "color": "C0"}],
              "puntos": [{"x": float(p.valor), "y": actual, "etiqueta": "valor base"}] if actual is not None else []}
    return {"parametro": parametro, "etiqueta": etiqueta, "unidad": p.unidad, "magnitud": magnitud,
            "x": [a for a, _b in pares], "y": [b for _a, b in pares], "fallidos": fallidos, "valorActual": float(p.valor),
            "actual": actual, "derivada": derivada,
            "grafico": grafico(curvas, etiqueta + (f" ({p.unidad})" if p.unidad else ""), magnitud)}


def validez(estado: str, fallos: list[str], corrida: dict | None, no_finitos: int = 0) -> dict:
    """{valido, nivel, titulo, texto}: una corrida es válida si el modelo está verificado y sus números son finitos (L8)."""
    if corrida is None or not corrida:
        return {"valido": False, "nivel": "inactivo", "titulo": "", "texto": "Sin corrida"}
    resultados = corrida.get("resultados", [])
    raros = [str(k) for k, v in resultados if isinstance(v, (int, float)) and not math.isfinite(float(v))]
    if raros or no_finitos:
        return {"valido": False, "nivel": "negativo", "titulo": "NO VÁLIDO",
                "texto": "El cálculo sale del dominio del modelo con estos parámetros: " + (", ".join(raros) if raros else f"{no_finitos} valores no finitos")
                         + ". Vuelve a valores dentro del rango que el modelo admite."}
    if estado == "diferencias":
        lista = ", ".join(fallos[:3]) + (f" y {len(fallos) - 3} más" if len(fallos) > 3 else "")
        return {"valido": False, "nivel": "negativo", "titulo": "NO VÁLIDO",
                "texto": f"Fallan {len(fallos)} verificación(es) del modelo ({lista}): sus resultados no se dan por buenos hasta que pasen."}
    if estado != "verificado":
        return {"valido": False, "nivel": "neutro", "titulo": "SIN VERIFICAR",
                "texto": "El modelo no está verificado con su archivo actual: verifica (Ctrl+T) antes de leer estos resultados como válidos."}
    return {"valido": True, "nivel": "positivo", "titulo": "", "texto": "Verificado: todas las verificaciones del modelo pasan."}
