#!/usr/bin/env python3
"""studio/muestra.py — un laboratorio de muestra para las pruebas y las capturas de Simuladores Studio.

Nunca los modelos reales ni `catalogo.json` del repo. En una carpeta temporal copia el MOTOR real (`base.py`,
`navegador.py`, `graficos.py`, `laboratorio.py`, `reporte.py`, `fuentes.py`, `app.py`, `main.py`) y crea una disciplina
`demo` con su `config.py` (que no importa matplotlib: correr y verificar funcionan con el Python del sistema), un
`main.py` (el de macro, copiado: sus CLI necesitan matplotlib) y dos modelos: `d01`, un mercado lineal (dos rectas y
su equilibrio) que pasa sus verificaciones, `d02`, un flujo en barras con una verificación que falla a propósito, y `d03`, un modelo dinámico (la evolución temporal del
capital hacia su estado estacionario, con x = el tiempo) que pasa.
`catalogo.json` se genera con el `main.py` real. Devuelve las variables de entorno con las que el studio ve la muestra
(`SIMULADORES_STUDIO_RAIZ`) y un HOME temporal (ninguna ruta de la máquina en pantalla).

    from muestra import crear
    m = crear(Path(carpeta))      # m.raiz, m.entorno: SIMULADORES_STUDIO_RAIZ, HOME, XDG_*…
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent
MOTOR = ("base.py", "navegador.py", "graficos.py", "laboratorio.py", "reporte.py", "fuentes.py", "app.py", "main.py")

CONFIG = '''"""demo/config.py — la disciplina de muestra de Simuladores Studio (sin matplotlib: correr y verificar bastan)."""
from pathlib import Path

DIR_BASE = Path(__file__).resolve().parent
DIR_MODELOS = DIR_BASE / "modelos"
DIR_SALIDAS = DIR_BASE / "salidas"
PROCEDENCIA_POR_DEFECTO = "modelos de muestra del studio: calibraciones didácticas, sin fuente"
AREA = "demo"
AZUL = "#1F3864"
AZUL2 = "#2E5496"
ROJO = "#9E2A2B"
DORADO = "#C9A227"
GRIS = "#B0B7C3"
VERDE = "#3A7D44"
DPI = 100
TAMANO_FIGURA = (8.0, 5.0)
SECCIONES = {1: "I · Mercados", 2: "II · Flujos"}
APP_VENTANA = "Laboratorio de muestra"
APP_NOMBRE = "LABORATORIO DE MUESTRA"
APP_TITULO = "Laboratorio de muestra"
APP_RECORRIDO = "Elige un modelo."
APP_UNIDAD_NIVEL = "Nivel"
APP_PASO_RESULTADOS = "El equilibrio"
APP_PANEL_RESULTADOS = "EQUILIBRIO"
APP_PASO_COMPARACION = "Comparación"


def aplicar_estilo():
    """La tipografía de las figuras (graficos.py la pide al importarse): matplotlib solo aquí, si está."""
    import matplotlib
    matplotlib.rcParams.update({"font.family": "serif", "mathtext.fontset": "stix", "axes.unicode_minus": False, "font.size": 11})
'''

D01 = '''"""demo/modelos/nivel_01/d01_mercado_lineal.py — oferta y demanda lineales (nivel 1): el modelo de muestra que pasa."""
import numpy as np

from base import Ecuacion, Escenario, Ficha, Modelo, Parametro, Verificacion
import config

_P0 = {"a": 100.0, "b": 2.0, "c": 20.0, "d": 2.0}


def _equilibrio(p):
    q = (p["a"] - p["c"]) / (p["b"] + p["d"])
    return q, p["a"] - p["b"] * q


def _curvas(p):
    q = np.linspace(0, 50, 101)
    qe, pe = _equilibrio(p)
    return {"lineas": {"Demanda $D$": (q, p["a"] - p["b"] * q, config.AZUL2), "Oferta $S$": (q, p["c"] + p["d"] * q, config.ROJO)},
            "equilibrio": (qe, pe), "anotacion": f"$Q^* = {qe:.1f}$, $P^* = {pe:.1f}$"}


def _resultados(p):
    qe, pe = _equilibrio(p)
    return {"Q* (cantidad)": qe, "P* (precio)": pe, "ingreso P*·Q*": pe * qe}


def _v_cruce():
    qe, pe = _equilibrio(_P0)
    dif = abs((_P0["a"] - _P0["b"] * qe) - (_P0["c"] + _P0["d"] * qe))
    return dif < 1e-9, f"en Q* la demanda iguala a la oferta (dif={dif:.1e}, esperado 0)"


def _v_positivo():
    qe, pe = _equilibrio(_P0)
    return qe > 0 and pe > 0, f"Q* = {qe:.2f} y P* = {pe:.2f} son positivos"


MODELO = Modelo(
    id="d01", nivel=1, nombre="Mercado lineal", xlabel="Cantidad ($Q$)", ylabel="Precio ($P$)",
    parametros=[Parametro("a", _P0["a"], 50, 200, 5, "Demanda autónoma a", "demanda", "el precio al que nadie compra", "u. m."),
                Parametro("b", _P0["b"], 0.5, 5, 0.1, "Pendiente de la demanda b", "demanda"),
                Parametro("c", _P0["c"], 0, 80, 5, "Costo mínimo c", "oferta"),
                Parametro("d", _P0["d"], 0.5, 5, 0.1, "Pendiente de la oferta d", "oferta")],
    curvas=_curvas, resultados=_resultados,
    ficha=Ficha(pregunta="¿Dónde se cruzan la oferta y la demanda, y qué mueve el cruce?",
                contexto="El modelo de muestra: dos rectas y su cruce.", autores="Marshall (1890), como ilustración.",
                supuestos=["Demanda y oferta lineales.", "Un solo bien."],
                ecuaciones=[Ecuacion("P = a - b\\\\,Q", "demanda", "el precio cae con la cantidad"),
                            Ecuacion("P = c + d\\\\,Q", "oferta", "el precio sube con la cantidad"),
                            Ecuacion("Q^* = \\\\frac{a - c}{b + d}", "equilibrio", "el cruce")],
                intuicion="Si el precio está por encima del cruce sobra producto; por debajo, falta.",
                limitaciones=["Es lineal."], evolucion="Nada: es la muestra."),
    escenarios=[Escenario("mas_demanda", "la demanda autónoma sube de 100 a 130", {"a": 130.0}, "suben el precio y la cantidad.", cadena=["↑a", "D → derecha", "↑Q*, ↑P*"]),
                Escenario("mas_costo", "el costo mínimo sube de 20 a 40", {"c": 40.0}, "sube el precio y cae la cantidad.", cadena=["↑c", "S → arriba", "↓Q*, ↑P*"])],
    verificaciones=[Verificacion("demanda = oferta en Q*", _v_cruce), Verificacion("equilibrio positivo", _v_positivo)],
)
'''

D02 = '''"""demo/modelos/nivel_02/d02_flujo_barras.py — un flujo en barras (nivel 2): el modelo de muestra con una diferencia."""
from base import Escenario, Ficha, Modelo, Parametro, Verificacion
import config

_P0 = {"I": 100.0, "G": 80.0, "s": 0.2}


def _flujos(p):
    Y = (p["I"] + p["G"]) / p["s"]
    return {"Y": Y, "S": p["s"] * Y}


def _curvas(p):
    f = _flujos(p)
    return {"barras": (["$S$", "$I$", "$G$"], [f["S"], p["I"], p["G"]], [config.ROJO, config.VERDE, config.VERDE]),
            "anotacion": f"$Y^* = {f['Y']:,.0f}$"}


def _resultados(p):
    f = _flujos(p)
    return {"Y* (producto)": f["Y"], "S (ahorro)": f["S"]}


def _v_igualdad():
    f = _flujos(_P0)
    dif = abs(f["S"] - (_P0["I"] + _P0["G"]))
    return dif < 1e-9, f"S = I + G en Y* (dif={dif:.1e})"


def _v_falla():
    f = _flujos(_P0)
    return f["Y"] > 1000, f"Y* = {f['Y']:.0f}; esperado > 1000 (falla a propósito: la muestra con diferencias)"


MODELO = Modelo(
    id="d02", nivel=2, nombre="Flujo en barras", xlabel="", ylabel="Flujo (u. m.)",
    parametros=[Parametro("I", _P0["I"], 0, 300, 10, "Inversión I", "inyecciones"), Parametro("G", _P0["G"], 0, 300, 10, "Gasto G", "inyecciones"),
                Parametro("s", _P0["s"], 0.05, 0.6, 0.05, "Propensión a ahorrar s", "filtraciones")],
    curvas=_curvas, resultados=_resultados,
    ficha=Ficha(pregunta="¿Qué producto sostiene el circuito?", contexto="La muestra en barras.", autores="Nadie.", supuestos=["Proporción fija."],
                ecuaciones=[], intuicion="Las filtraciones igualan a las inyecciones."),
    escenarios=[Escenario("mas_inversion", "la inversión sube de 100 a 150", {"I": 150.0}, "el circuito se expande.")],
    verificaciones=[Verificacion("S = I + G en Y*", _v_igualdad), Verificacion("Y* mayor que 1000", _v_falla)],
)
'''


D03 = '''"""demo/modelos/nivel_03/d03_capital_dinamico.py — la acumulación de capital en el tiempo (nivel 3): el modelo dinámico de la muestra."""
import numpy as np

from base import Ecuacion, Escenario, Ficha, Modelo, Parametro, Verificacion
import config

_P0 = {"s": 0.25, "delta": 0.08, "A": 1.0, "alfa": 0.33, "K0": 1.0, "T": 60.0}


def _estacionario(p):
    return (p["s"] * p["A"] / p["delta"]) ** (1 / (1 - p["alfa"]))


def _trayectoria(p):
    T = int(p["T"])
    k = np.empty(T + 1)
    k[0] = p["K0"]
    for t in range(T):
        k[t + 1] = k[t] + p["s"] * p["A"] * k[t] ** p["alfa"] - p["delta"] * k[t]
    return np.arange(T + 1), k


def _curvas(p):
    t, k = _trayectoria(p)
    ke = _estacionario(p)
    return {"lineas": {"capital $K_t$": (t, k, config.AZUL2), "estado estacionario $K^*$": (t, np.full_like(k, ke), config.DORADO)},
            "puntos": [(int(t[-1]), float(k[-1]), "$K_T$")], "anotacion": f"$K^* = {ke:.2f}$"}


def _resultados(p):
    t, k = _trayectoria(p)
    ke = _estacionario(p)
    mitad = next((int(i) for i, v in zip(t, k) if abs(v - ke) <= abs(k[0] - ke) / 2), int(t[-1]))
    return {"K* (estacionario)": ke, "K_T (al final)": float(k[-1]), "periodos hasta la mitad del camino": mitad}


def _v_estacionario():
    ke = _estacionario(_P0)
    resto = _P0["s"] * _P0["A"] * ke ** _P0["alfa"] - _P0["delta"] * ke
    return abs(resto) < 1e-9, f"en K* la inversión iguala a la depreciación (resto={resto:.1e})"


def _v_converge():
    p = dict(_P0, T=400.0)
    t, k = _trayectoria(p)
    ke = _estacionario(p)
    return abs(k[-1] - ke) / ke < 1e-3, f"K_400 = {k[-1]:.4f} frente a K* = {ke:.4f}"


MODELO = Modelo(
    id="d03", nivel=3, nombre="Capital en el tiempo", xlabel="Tiempo ($t$, periodos)", ylabel="Capital por trabajador ($K$)",
    parametros=[Parametro("s", _P0["s"], 0.05, 0.6, 0.01, "Tasa de ahorro s", "conducta", "fracción del producto que se ahorra"),
                Parametro("delta", _P0["delta"], 0.01, 0.2, 0.01, "Depreciación δ", "tecnología", "fracción del capital que se gasta cada periodo"),
                Parametro("A", _P0["A"], 0.5, 2.0, 0.05, "Productividad A", "tecnología"),
                Parametro("alfa", _P0["alfa"], 0.2, 0.6, 0.01, "Elasticidad del capital α", "tecnología"),
                Parametro("K0", _P0["K0"], 0.1, 20, 0.1, "Capital inicial K₀", "condición inicial"),
                Parametro("T", _P0["T"], 10, 150, 5, "Horizonte T", "simulación", "", "periodos")],
    curvas=_curvas, resultados=_resultados,
    ficha=Ficha(pregunta="¿Hacia dónde va el capital y qué tan rápido llega?", contexto="La ecuación de acumulación de Solow (1956), como muestra dinámica.",
                autores="Solow (1956), Swan (1956).", supuestos=["Rendimientos decrecientes del capital.", "Ahorro y depreciación constantes."],
                ecuaciones=[Ecuacion("K_{t+1} = K_t + s\\\\,A\\\\,K_t^{\\\\alpha} - \\\\delta\\\\,K_t", "acumulación", "el capital crece con la inversión y se gasta con la depreciación"),
                            Ecuacion("K^* = (s A / \\\\delta)^{1/(1-\\\\alpha)}", "estado estacionario", "donde la inversión iguala a la depreciación")],
                intuicion="Con poco capital, cada unidad rinde mucho y el capital crece rápido; cerca de K* la inversión apenas cubre la depreciación.",
                limitaciones=["Sin progreso técnico: el crecimiento se detiene en K*."], evolucion="El modelo de Solow completo."),
    escenarios=[Escenario("mas_ahorro", "la tasa de ahorro sube de 0,25 a 0,35", {"s": 0.35}, "K* sube y el capital crece más tiempo.", cadena=["↑s", "↑inversión", "↑K*"])],
    verificaciones=[Verificacion("K* anula el cambio", _v_estacionario), Verificacion("la trayectoria converge a K*", _v_converge)],
)
'''


@dataclass
class Muestra:
    raiz: Path
    disciplina: Path
    entorno: dict = field(default_factory=dict)


def crear(raiz: Path) -> Muestra:
    raiz = Path(raiz)
    if raiz.exists():
        shutil.rmtree(raiz)
    raiz.mkdir(parents=True)
    for nombre in MOTOR:
        shutil.copy2(REPO / nombre, raiz / nombre)
    demo = raiz / "demo"
    (demo / "modelos" / "nivel_01").mkdir(parents=True)
    (demo / "modelos" / "nivel_02").mkdir(parents=True)
    (demo / "modelos" / "nivel_03").mkdir(parents=True)
    (demo / "docs").mkdir()
    (demo / "docs" / "laboratorio-demo.md").write_text("# Laboratorio de muestra\n\nDos modelos de juguete para las pruebas y las capturas del studio.\n", encoding="utf-8")
    (demo / "config.py").write_text(CONFIG, encoding="utf-8")
    shutil.copy2(REPO / "macro" / "main.py", demo / "main.py")
    (demo / "modelos" / "__init__.py").write_text('"""demo/modelos — los modelos de muestra, un paquete por nivel."""\n', encoding="utf-8")
    (demo / "modelos" / "nivel_01" / "__init__.py").write_text("", encoding="utf-8")
    (demo / "modelos" / "nivel_02" / "__init__.py").write_text("", encoding="utf-8")
    (demo / "modelos" / "nivel_03" / "__init__.py").write_text("", encoding="utf-8")
    (demo / "modelos" / "nivel_01" / "d01_mercado_lineal.py").write_text(D01, encoding="utf-8")
    (demo / "modelos" / "nivel_02" / "d02_flujo_barras.py").write_text(D02, encoding="utf-8")
    (demo / "modelos" / "nivel_03" / "d03_capital_dinamico.py").write_text(D03, encoding="utf-8")
    hogar = raiz / "hogar"
    for sub in (".config", ".cache", ".local/share", ".local/state"):
        (hogar / sub).mkdir(parents=True, exist_ok=True)
    entorno = {"SIMULADORES_STUDIO_RAIZ": str(raiz), "HOME": str(hogar), "XDG_CONFIG_HOME": str(hogar / ".config"), "XDG_CACHE_HOME": str(hogar / ".cache"),
               "XDG_DATA_HOME": str(hogar / ".local" / "share"), "XDG_STATE_HOME": str(hogar / ".local" / "state"), "LC_ALL": "C.UTF-8",
               "PYTHONDONTWRITEBYTECODE": "1", "MPLBACKEND": "Agg"}
    r = subprocess.run([sys.executable, str(raiz / "main.py"), "catalogo", "--aplicar"], cwd=str(raiz), capture_output=True, text=True, timeout=120,
                       env={**_entorno_base(), **entorno})
    if r.returncode != 0:
        raise RuntimeError(f"no se pudo generar el catálogo de la muestra:\n{r.stderr[-2000:]}")
    return Muestra(raiz=raiz, disciplina=demo, entorno=entorno)


def _entorno_base() -> dict:
    import os
    return {k: v for k, v in os.environ.items() if k not in ("SIMULADORES_STUDIO_RAIZ",)}


if __name__ == "__main__":
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "muestra-simuladores"
    m = crear(destino)
    print(m.raiz)
