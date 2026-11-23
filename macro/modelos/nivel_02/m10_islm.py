"""simuladores/macro/modelos/nivel_02/m10_islm.py — modelo IS-LM (Hicks) — nivel 2 del currículo.

Mercado de bienes (IS):  Y = C + I + G,  C = c0 + c1(Y−T),  I = I0 − b·r
  → r_IS(Y) = [c0 − c1·T + I0 + G − (1−c1)·Y] / b
Mercado de dinero (LM):  M/P = k·Y − h·r
  → r_LM(Y) = (k·Y − M/P) / h
Equilibrio: intersección. Política fiscal mueve G/T (IS); monetaria mueve M/P (LM).

Referencia teórica: modelo IS-LM estándar (Hicks 1937; cualquier manual de
macro intermedia). Procedencia: conocimiento macroeconómico general.
"""

import numpy as np

from base import Ecuacion, Ejercicio, Escenario, Ficha, Modelo, Parametro, Pedagogia, Resultado, Verificacion
import config


def _equilibrio(p):
    A = (1 - p["c1"]) + p["b"] * p["k"] / p["h"]
    B = p["c0"] - p["c1"] * p["T"] + p["I0"] + p["G"] + p["b"] * p["MP"] / p["h"]
    Y = B / A
    r = (p["k"] * Y - p["MP"]) / p["h"]
    return Y, r, A


def _curvas(p):
    Y = np.linspace(0, 1000, 400)
    r_is = (p["c0"] - p["c1"] * p["T"] + p["I0"] + p["G"] - (1 - p["c1"]) * Y) / p["b"]
    r_lm = (p["k"] * Y - p["MP"]) / p["h"]
    Y_eq, r_eq, _ = _equilibrio(p)
    return {"lineas": {"IS (bienes)": (Y, r_is, config.AZUL2),
                       "LM (dinero)": (Y, r_lm, config.ROJO)},
            "equilibrio": (Y_eq, r_eq)}


def _resultados(p):
    Y, r, A = _equilibrio(p)
    C = p["c0"] + p["c1"] * (Y - p["T"])
    I = p["I0"] - p["b"] * r
    return {"Y* (producto)": Y, "r* (tasa de interés)": r,
            "consumo C*": C, "inversión I*": I,
            "multiplicador fiscal dY/dG": 1 / A,
            "comprobación Y = C+I+G": C + I + p["G"]}


def _ecuaciones_calibradas(p):
    Y, r, _ = _equilibrio(p)
    return [f"$C = {p['c0']:.0f} + {p['c1']:.2f}\\,(Y - {p['T']:.0f})$",
            f"$I = {p['I0']:.0f} - {p['b']:.0f}\\,r$",
            f"$M/P = {p['MP']:.0f} = {p['k']:.2f}\\,Y - {p['h']:.0f}\\,r$",
            f"$Y^* = {Y:,.1f}, \\quad r^* = {r:.2f}$"]


_P0 = {"G": 200.0, "MP": 300.0, "T": 100.0, "c1": 0.6, "b": 20.0,
       "k": 0.5, "h": 10.0, "c0": 100.0, "I0": 150.0}


def _v_equilibrio():
    p = _P0
    Y, r, _ = _equilibrio(p)
    res_is = Y - (p["c0"] + p["c1"] * (Y - p["T"]) + p["I0"] - p["b"] * r + p["G"])
    res_lm = p["MP"] - (p["k"] * Y - p["h"] * r)
    ok = abs(res_is) < 1e-9 and abs(res_lm) < 1e-9
    return ok, f"Y*, r* satisfacen AMBOS mercados (residuos {res_is:.1e}, {res_lm:.1e})"


def _v_fiscal():
    Y0, r0, _ = _equilibrio(_P0)
    Y1, r1, _ = _equilibrio(dict(_P0, G=_P0["G"] + 50))
    I0_, I1_ = _P0["I0"] - _P0["b"] * r0, _P0["I0"] - _P0["b"] * r1
    ok = Y1 > Y0 and r1 > r0 and I1_ < I0_
    return ok, (f"↑G: Y sube ({Y0:,.0f}→{Y1:,.0f}), r sube ({r0:.2f}→{r1:.2f}) "
                f"y la inversión cae ({I0_:,.1f}→{I1_:,.1f}) — efecto expulsión")


def _v_monetaria():
    Y0, r0, _ = _equilibrio(_P0)
    Y1, r1, _ = _equilibrio(dict(_P0, MP=_P0["MP"] + 100))
    return (Y1 > Y0 and r1 < r0), f"↑M/P: Y sube ({Y0:,.0f}→{Y1:,.0f}) y r baja ({r0:.2f}→{r1:.2f})"


def _v_multiplicador_menor():
    _, _, A = _equilibrio(_P0)
    k_islm, k_simple = 1 / A, 1 / (1 - _P0["c1"])
    return k_islm < k_simple, (f"multiplicador IS-LM ({k_islm:.2f}) < multiplicador simple "
                               f"({k_simple:.2f}): la tasa de interés amortigua (vs m04)")


MODELO = Modelo(
    id="m10", nivel=2,
    nombre="Modelo IS-LM",
    parametros=[
        Parametro("G", _P0["G"], 0, 500, 10, "Gasto público G", grupo="política fiscal",
                  definicion="compras del gobierno; desplaza la IS", unidad="u.m."),
        Parametro("MP", _P0["MP"], 100, 600, 10, "Oferta real de dinero M/P", grupo="política monetaria",
                  definicion="saldos reales que fija el banco central; desplaza la LM", unidad="u.m."),
        Parametro("T", _P0["T"], 0, 400, 10, "Impuestos T", grupo="política fiscal",
                  definicion="impuestos de suma fija; entran vía renta disponible", unidad="u.m."),
        Parametro("c1", _P0["c1"], 0.1, 0.9, 0.05, "Propensión a consumir c1", grupo="mercado de bienes",
                  definicion="fracción re-gastada de cada unidad de renta disponible"),
        Parametro("b", _P0["b"], 5, 50, 1, "Sensibilidad de I a r (b)", grupo="mercado de bienes",
                  definicion="inversión descartada por cada punto de tasa"),
        Parametro("k", _P0["k"], 0.1, 1.0, 0.05, "Demanda de dinero por Y (k)", grupo="mercado de dinero",
                  definicion="liquidez requerida por las transacciones"),
        Parametro("h", _P0["h"], 2, 30, 1, "Demanda de dinero por r (h)", grupo="mercado de dinero",
                  definicion="liquidez que se libera cuando la tasa premia los bonos"),
        Parametro("c0", _P0["c0"], 0, 300, 10, "Consumo autónomo c0", grupo="mercado de bienes",
                  definicion="consumo independiente del ingreso corriente"),
        Parametro("I0", _P0["I0"], 0, 400, 10, "Inversión autónoma I0", grupo="mercado de bienes",
                  definicion="ánimo inversor (animal spirits) independiente de la tasa"),
    ],
    curvas=_curvas,
    resultados=_resultados,
    ecuaciones_calibradas=_ecuaciones_calibradas,
    ficha=Ficha(
        pregunta=("¿Qué ocurre con el producto y la tasa de interés cuando el gobierno "
                  "aumenta el gasto público — y quién termina financiándolo?"),
        variables=[("Y", "producto/ingreso — endógena"),
                   ("r", "tasa de interés — endógena"),
                   ("C, I", "consumo e inversión — endógenas (derivadas de Y y r)"),
                   ("G, T", "instrumentos fiscales — exógenas"),
                   ("M/P", "oferta real de dinero — exógena (instrumento monetario)")],
        derivacion=[
            "Y = c_0 + c_1(Y-T) + I_0 - b\\,r + G",
            "(1-c_1)\\,Y = c_0 - c_1 T + I_0 + G - b\\,r",
            "r = \\frac{k\\,Y - M/P}{h} \\;\\; (LM)",
            "(1-c_1)\\,Y = c_0 - c_1T + I_0 + G - \\frac{b}{h}\\Big(k\\,Y - \\frac{M}{P}\\Big)",
            "\\Big[(1-c_1) + \\frac{b\\,k}{h}\\Big]\\,Y = c_0 - c_1T + I_0 + G + \\frac{b}{h}\\,\\frac{M}{P}",
            "Y^* = \\frac{c_0 - c_1T + I_0 + G + \\frac{b}{h}\\frac{M}{P}}{(1-c_1) + \\frac{b\\,k}{h}}",
        ],
        contexto=("Un año después de la Teoría General, John Hicks ('Mr. Keynes and the "
                  "Classics', 1937) tradujo el libro a un sistema de dos ecuaciones y dos "
                  "incógnitas (Y, r) que se volvió el lenguaje común de la macroeconomía "
                  "de posguerra. Corrige la carencia central del nivel 1: la inversión ya "
                  "no es exógena — depende de una tasa de interés que se determina en el "
                  "mercado de dinero, simultáneamente con el ingreso."),
        autores=("Hicks (1937); difundido y ampliado por Hansen (síntesis neoclásica, "
                 "años 40-50). Fue el caballo de batalla de la política macro hasta los 70."),
        supuestos=[
            "Precios fijos (corto plazo estricto): todo ajuste es por cantidades y tasa de interés.",
            "Economía cerrada: sin tipo de cambio ni flujos de capital (los añade Mundell-Fleming, m49).",
            "La inversión responde negativamente a r; la demanda de dinero sube con Y y baja con r.",
            "Oferta monetaria exógena controlada por el banco central (los bancos centrales modernos fijan r: ver IS-MP, m51).",
            "Sin expectativas de inflación: r nominal = r real.",
        ],
        ecuaciones=[
            Ecuacion("Y = c_0 + c_1(Y-T) + I_0 - b\\,r + G", "curva IS",
                     "equilibrio del mercado de bienes para cada r: hereda el consumo keynesiano "
                     "(m03) y el multiplicador (m04), pero ahora la inversión cae cuando r sube."),
            Ecuacion("\\frac{M}{P} = k\\,Y - h\\,r", "curva LM",
                     "equilibrio del mercado de dinero: la demanda de saldos reales sube con las "
                     "transacciones (k·Y) y baja con el costo de oportunidad de tener dinero (h·r)."),
            Ecuacion("Y^* = \\frac{c_0 - c_1 T + I_0 + G + \\frac{b}{h}\\,\\frac{M}{P}}{(1-c_1) + \\frac{b\\,k}{h}}",
                     "equilibrio general del sistema",
                     "resolver ambas curvas a la vez: el denominador muestra POR QUÉ el multiplicador "
                     "IS-LM es menor que el simple — el término bk/h es el freno de la tasa de interés."),
        ],
        intuicion=("Dos mercados se disciplinan mutuamente. Una expansión fiscal eleva el "
                   "ingreso, pero el mayor ingreso eleva la demanda de dinero y con ella "
                   "la tasa de interés, lo que expulsa inversión privada: el multiplicador "
                   "del nivel 1 era una sobreestimación. La política monetaria opera al "
                   "revés: más dinero baja r y estimula la inversión."),
        equilibrio=("Intersección IS-LM: único par (Y*, r*) que equilibra bienes y dinero "
                    "a la vez. Estable con IS decreciente y LM creciente: fuera del cruce, "
                    "exceso de demanda/oferta en algún mercado empuja hacia él."),
        limitaciones=[
            "Sin nivel de precios: no puede hablar de inflación — su extensión natural es AD-AS (m20-m23).",
            "Sin expectativas: vulnerable a la crítica de Lucas (1976) — los parámetros no son invariantes a la política.",
            "Economía cerrada: inútil para economías abiertas pequeñas como Perú sin la extensión Mundell-Fleming (m49).",
            "Trata la política monetaria como control de M, cuando los bancos centrales modernos fijan la tasa (BCRP incluido): versión moderna en IS-MP (m51).",
            "Estático: describe equilibrios, no la trayectoria temporal entre ellos.",
        ],
        evolucion=("Del IS-LM salen tres caminos del currículo: el efecto expulsión (m11) "
                   "y la trampa de liquidez (m12) como casos límite; AD-AS (m20-m25) al "
                   "endogenizar precios; y Mundell-Fleming (m49) al abrir la economía. "
                   "Su versión moderna con regla de tasa de interés es IS-MP (m51) y el "
                   "modelo nuevo keynesiano (m53-m56)."),
        pedagogia=Pedagogia(
            resultados=[
                Resultado("r1", "relacional",
                          "Explica, con el equilibrio simultáneo del mercado de bienes y del de dinero, por qué una "
                          "expansión fiscal eleva la tasa de interés y desplaza inversión privada (efecto expulsión)."),
                Resultado("r2", "relacional",
                          "Compara los efectos de una expansión fiscal y de una monetaria sobre el producto, la tasa "
                          "de interés y la inversión, y relaciona el tamaño del multiplicador fiscal con la "
                          "sensibilidad de la demanda de dinero a la tasa de interés (h)."),
            ],
            ejercicios=[
                Ejercicio(
                    "e1", "r1", escenario="expansion_fiscal", bloom="analizar",
                    predecir=("El gobierno sube el gasto de 200 a 250 sin cambiar la oferta de dinero. ¿Qué pasa con "
                              "el producto, la tasa de interés y la inversión privada?"),
                    item={"tipo": "opcion", "bloom": "comprender", "dificultad": "media",
                          "enunciado": ("Si el gasto público sube de 200 a 250 con M/P fija, ¿qué le pasa a la "
                                        "inversión privada I*?"),
                          "opciones": ["Sube, porque sube el producto", "Baja, porque sube la tasa de interés",
                                       "No cambia, porque la inversión autónoma I0 no cambió"],
                          "respuesta": "Baja, porque sube la tasa de interés",
                          "errores": [
                              {"opcion": "Sube, porque sube el producto",
                               "error": ("traslada la intuición del nivel 1; aquí la inversión depende solo de la "
                                         "tasa (I = I0 − b·r), y la tasa sube con el ingreso")},
                              {"opcion": "No cambia, porque la inversión autónoma I0 no cambió",
                               "error": "olvida que la tasa de interés es endógena: se determina junto con el producto"},
                          ]},
                    observar=("cómo se corre la IS, el nuevo cruce con la LM y las cifras «Y* (producto)», «r* (tasa de "
                              "interés)» e «inversión I*»."),
                    explicar=("¿Por qué sube la tasa de interés si el banco central no hizo nada? ¿Por qué el "
                              "producto sube menos que los 50 del gasto?"),
                    respuesta=("La IS se corre a la derecha y el producto sube de 707 a 743. El mayor ingreso eleva la "
                               "demanda de dinero (k·Y); con M/P fija, la tasa sube de 5,36 a 7,14 para que el público "
                               "se conforme con los mismos saldos reales. La inversión (I = I0 − b·r) cae de 42,9 a "
                               "7,1. El producto sube 35,7: menos que el impulso y muy por debajo de los 125 del "
                               "multiplicador simple 1/(1 − c1) = 2,5, porque la tasa expulsa inversión privada."),
                    error_comun=("Creer que la tasa de interés solo la mueve el banco central, o que todo gasto público "
                                 "adicional se suma al producto sin tocar la inversión."),
                    espera={"Y* (producto)": "↑", "r* (tasa de interés)": "↑", "inversión I*": "↓"},
                    valores={"Y* (producto)": 742.86, "r* (tasa de interés)": 7.143, "inversión I*": 7.143}),
                Ejercicio(
                    "e2", "r2", escenario="expansion_monetaria", bloom="analizar",
                    predecir=("Ahora el gasto vuelve a 200 y el banco central sube la oferta real de dinero de 300 a "
                              "400. ¿En qué se parece y en qué se diferencia del resultado de la expansión fiscal?"),
                    item={"tipo": "opcion", "bloom": "comprender", "dificultad": "baja",
                          "enunciado": "Si la oferta real de dinero sube de 300 a 400, ¿cómo cambian Y* y r*?",
                          "opciones": ["Y sube y r sube", "Y sube y r baja", "Y no cambia y r baja", "Y baja y r baja"],
                          "respuesta": "Y sube y r baja",
                          "errores": [
                              {"opcion": "Y sube y r sube",
                               "error": "traslada la firma de la política fiscal a la monetaria"},
                              {"opcion": "Y no cambia y r baja",
                               "error": ("mira solo el mercado de dinero y olvida que la tasa menor estimula la "
                                         "inversión y, por el multiplicador, el producto")},
                              {"opcion": "Y baja y r baja",
                               "error": "confunde el desplazamiento de la LM a la derecha con una contracción"},
                          ]},
                    observar="cómo se corre la LM y las cifras «Y* (producto)», «r* (tasa de interés)» e «inversión I*».",
                    explicar=("Compara con el ejercicio anterior: ¿por qué las dos políticas suben el producto pero "
                              "mueven la tasa de interés y la inversión en sentidos opuestos?"),
                    respuesta=("La LM se corre a la derecha: con más saldos reales, la tasa debe bajar (de 5,36 a 2,5) "
                               "para que el público quiera tenerlos; la inversión sube de 42,9 a 100 y, por el "
                               "multiplicador, el producto sube de 707 a 850. La política fiscal empuja la demanda de "
                               "bienes y la tasa sube como consecuencia; la monetaria baja la tasa y la demanda sube "
                               "como consecuencia: la primera expulsa inversión, la segunda la atrae."),
                    error_comun="Pensar que toda política expansiva tiene la misma firma sobre la tasa de interés.",
                    espera={"Y* (producto)": "↑", "r* (tasa de interés)": "↓", "inversión I*": "↑"},
                    valores={"Y* (producto)": 850.0, "r* (tasa de interés)": 2.5, "inversión I*": 100.0}),
                Ejercicio(
                    "e3", "r2", cambios={"h": 30.0}, bloom="evaluar",
                    predecir=("Si la demanda de dinero se vuelve más sensible a la tasa de interés (h sube de 10 a 30), "
                              "¿el multiplicador fiscal dY/dG sube o baja?"),
                    item={"tipo": "opcion", "bloom": "analizar", "dificultad": "discriminante",
                          "enunciado": ("Si h, la sensibilidad de la demanda de dinero a la tasa, sube de 10 a 30, "
                                        "¿qué le pasa al multiplicador fiscal dY/dG?"),
                          "opciones": ["Sube, y se acerca al multiplicador simple 1/(1 − c1)",
                                       "Baja, porque el dinero pierde eficacia",
                                       "No cambia: h es del mercado de dinero y el multiplicador, del de bienes"],
                          "respuesta": "Sube, y se acerca al multiplicador simple 1/(1 − c1)",
                          "errores": [
                              {"opcion": "Baja, porque el dinero pierde eficacia",
                               "error": ("mezcla la eficacia de la política monetaria (que sí baja con h alto) con la "
                                         "de la fiscal")},
                              {"opcion": "No cambia: h es del mercado de dinero y el multiplicador, del de bienes",
                               "error": ("no ve que el equilibrio es simultáneo: el denominador del multiplicador, "
                                         "(1 − c1) + b·k/h, lleva h")},
                          ]},
                    observar="la pendiente de la LM y la cifra «multiplicador fiscal dY/dG».",
                    explicar=("¿Por qué una LM más plana hace más eficaz la política fiscal? ¿Qué pasaría en el límite, "
                              "si h fuera enorme?"),
                    respuesta=("El multiplicador es 1/[(1 − c1) + b·k/h]: con h = 30 pasa de 0,71 a 1,36. Si la demanda "
                               "de dinero responde mucho a la tasa, basta un alza pequeña de r para liberar los saldos "
                               "que pide el mayor ingreso: la LM es más plana, la tasa sube poco y expulsa poca "
                               "inversión. En el límite (h muy grande, la trampa de liquidez de m12) la tasa no sube y "
                               "el multiplicador tiende al simple, 1/(1 − c1) = 2,5."),
                    error_comun=("Tratar los dos mercados por separado, como si un parámetro del mercado de dinero no "
                                 "pudiera cambiar el efecto de la política fiscal."),
                    espera={"multiplicador fiscal dY/dG": "↑"},
                    valores={"multiplicador fiscal dY/dG": 1.364}),
            ],
            origen={"autor": "llm", "herramienta": "Claude Code (Claude Opus 5.5)", "fecha": "2026-11-24",
                    "verificacion": "pendiente"},
            pendientes=[
                "confirmar el nivel SOLO de r1 y r2 y llevarlos a los raN de macroeconomia-i (tema 3.4 «Modelo "
                "IS-LM»); el curso aún no declara `alineamiento:`",
                "con la calibración del modelo, G por encima de 260 (con M/P = 300) deja la inversión I* bajo cero, "
                "un artefacto de la especificación lineal; advertir al alumno si explora más allá de e1",
            ]),
    ),
    escenarios=[
        Escenario("expansion_fiscal", "el gasto público sube de 200 a 250",
                  {"G": 250.0},
                  "IS se desplaza a la derecha: Y y r suben; parte del impulso se pierde "
                  "en inversión expulsada (crowding out, m11). Con shocks grandes esta "
                  "especificación lineal puede llevar I* por debajo de cero — artefacto "
                  "del modelo, no economía.",
                  cadena=["↑G", "↑ demanda de bienes", "IS → derecha", "↑Y (multiplicador)",
                          "↑ demanda de dinero k·Y", "M/P fija ⇒ ↑r", "↓I = −b·Δr",
                          "expulsión parcial (m11)"]),
        Escenario("expansion_monetaria", "la oferta real de dinero sube de 300 a 400",
                  {"MP": 400.0},
                  "LM se desplaza a la derecha: Y sube con r MENOR — estimula la "
                  "inversión en vez de expulsarla.",
                  cadena=["↑M/P", "exceso de liquidez", "compra de bonos ⇒ ↑ precio",
                          "↓r", "LM → derecha", "↑I", "↑Y (multiplicador)"]),
        Escenario("contraccion_monetaria", "el banco central retira liquidez (M/P: 300→200)",
                  {"MP": 200.0},
                  "LM a la izquierda: r sube y el producto cae — la receta clásica "
                  "contra el sobrecalentamiento.",
                  cadena=["↓M/P", "escasez de liquidez", "venta de bonos", "↑r",
                          "LM → izquierda", "↓I", "↓Y"]),
        Escenario("politica_mixta", "expansión fiscal CON acomodo monetario",
                  {"G": 300.0, "MP": 400.0},
                  "si el banco central acomoda, la tasa casi no sube y el multiplicador "
                  "se acerca al del nivel 1: la mezcla de políticas importa tanto como "
                  "cada política.",
                  cadena=["↑G (IS → derecha)", "↑M/P (LM → derecha)",
                          "las presiones sobre r se compensan", "Δr pequeño",
                          "casi sin expulsión", "ΔY cercano a k·ΔG (m04)"]),
    ],
    verificaciones=[
        Verificacion("(Y*, r*) satisface IS y LM a la vez", _v_equilibrio),
        Verificacion("expansión fiscal: ↑Y, ↑r, ↓I (expulsión)", _v_fiscal),
        Verificacion("expansión monetaria: ↑Y, ↓r", _v_monetaria),
        Verificacion("multiplicador IS-LM < multiplicador simple", _v_multiplicador_menor),
    ],
    notas="Expansión fiscal (↑G) desplaza IS→derecha (↑Y, ↑r). Expansión "
          "monetaria (↑M/P) desplaza LM→derecha (↑Y, ↓r).",
)
