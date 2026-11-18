"""tests/studio/test_rediseno.py — la forma propia aprobada de Simuladores Studio (2026-11-18, `docs/decisiones.md`): el
laboratorio (catálogo a la izquierda, las curvas en vivo con el equilibrio marcado al centro, los parámetros a la
derecha, las verificaciones contra la teoría con su fuente al pie), cero colores, radios ni letras propios en el QML,
los avisos por Mensajes de la base (sin acciones: las notificaciones de KDE) y las pistas efímeras a la barra de
estado, y las fórmulas que siguen el cambio de claro a oscuro. Todo sobre el laboratorio de muestra."""
from __future__ import annotations

import json
import re

import pytest

from conftest import STUDIO, correr_python, entorno_gui, requiere_binding, requiere_sistema

QML = STUDIO / "sim_app" / "qml"


def _sin_comentarios(texto: str) -> list[tuple[int, str]]:
    return [(n, l.split("//")[0]) for n, l in enumerate(texto.splitlines(), 1)]


def test_qml_sin_colores_radios_ni_letra_propios():
    patrones = [r'"#[0-9a-fA-F]{3,8}"', r"\bQt\.(rgba|rgb|hsla|hsva|lighter|darker|tint)\s*\(", r"\bradius\s*:",
                r"\bfont\.(pointSize|pixelSize)\s*:", r"\bfont\.family\s*:(?!\s*Kirigami\.Theme\.)"]
    malos = []
    for qml in QML.rglob("*.qml"):
        for n, linea in _sin_comentarios(qml.read_text(encoding="utf-8")):
            if any(re.search(p, linea) for p in patrones):
                malos.append(f"{qml.relative_to(STUDIO)}:{n}: {linea.strip()}")
    assert not malos, "\n".join(malos)


def test_avisos_por_la_base_sin_globos_propios():
    """Ningún toast, popup, banner ni InlineMessage propio: los avisos van a Mensajes (Plasma), las pistas a la barra."""
    for qml in QML.rglob("*.qml"):
        codigo = "\n".join(l for _n, l in _sin_comentarios(qml.read_text(encoding="utf-8")))
        assert "InlineMessage" not in codigo and "ToolTip.show(" not in codigo, qml
        assert not re.search(r"\b(Popup|Drawer|Kirigami\.OverlaySheet)\s*\{", codigo), qml
    main = (QML / "Main.qml").read_text(encoding="utf-8")
    assert main.count("mensajes.mostrar(") == 1                                   # solo `avisar`: lo demás pasa por ella
    assert 'if (tipo === "pista") pista(texto)' in main and "contexto: ventana.pistaActual || espacio.contexto" in main


def test_la_forma_del_laboratorio():
    main = (QML / "Main.qml").read_text(encoding="utf-8")
    orden = [main.index(x) for x in ("CatalogoModelos {", "EspacioSimulacion {}", "PanelParametros {", "BandaVerificaciones {")]
    assert orden == sorted(orden)                                                 # izquierda, centro, derecha, pie
    assert "function onTextColorChanged() { modelos.fijarColorTexto(" in main     # las fórmulas siguen el tema en vivo
    assert "EtiquetaNivel {" in main                                              # la validez, con la etiqueta de la base
    espacio = (QML / "componentes" / "EspacioSimulacion.qml").read_text(encoding="utf-8")
    assert "Equilibrio E: " in espacio and "Kirigami.Theme.highlightColor" in espacio   # el mismo punto que marca GraficoXY
    banda = (QML / "componentes" / "BandaVerificaciones.qml").read_text(encoding="utf-8")
    assert "fuenteVerificaciones" in banda and "verificacionesModelo" in banda


@pytest.fixture
def piezas(app, muestra_sesion, ajustes_temporales):
    from gui_comun.consola import Consola
    from gui_comun.tareas import Tareas
    from sim_app.controladores.ajustes import Ajustes
    from sim_app.controladores.espacio import Espacio
    from sim_app.controladores.modelos import Modelos
    from sim_app.controladores.operaciones import Operaciones
    consola = Consola()
    tareas = Tareas(consola)
    ajustes = Ajustes()
    espacio = Espacio(consola, ajustes)
    cache = ajustes_temporales / "cache" / "studio"
    modelos = Modelos(espacio, consola, cache=cache, datos=ajustes_temporales / "datos", raiz=muestra_sesion.raiz)
    modelos.verificar_al_abrir = False
    operaciones = Operaciones(espacio, modelos, ajustes, consola, tareas, cache=cache)
    return dict(modelos=modelos, operaciones=operaciones)


@requiere_binding
def test_pistas_a_la_barra_y_la_fuente_de_las_verificaciones(piezas):
    m, o = piezas["modelos"], piezas["operaciones"]
    avisos = []
    m.aviso.connect(lambda texto, tipo: avisos.append((texto, tipo)))
    o.aviso.connect(lambda texto, tipo: avisos.append((texto, tipo)))
    assert m.correr() is False and m.verificar() is False
    assert avisos and all(t == "pista" for _x, t in avisos), avisos              # «Elige primero un modelo»: efímero
    m.irA("demo/d01")
    assert m.fuenteVerificaciones == ""                                           # sin verificar todavía
    assert m.verificar() is True
    assert m.fuenteVerificaciones == "modelos de muestra del studio: calibraciones didácticas, sin fuente"
    m.aplicarEscenarioPorIndice(1)                                                # mas_demanda: a = 130
    assert m.correr() is True
    assert m.grafico["equilibrio"] == {"x": pytest.approx(27.5), "y": pytest.approx(75.0)}
    assert m.graficoBase["equilibrio"] == {"x": pytest.approx(20.0), "y": pytest.approx(60.0)}


VENTANA = """
import sys, json; sys.path.insert(0, sys.argv[1])
from sim_app import aplicacion
from gui_comun.nucleo import Aplicacion
from gui_comun.qt import QObject, QTimer
app = Aplicacion("simuladores-studio", "Simuladores Studio", version="prueba", organizacion="simuladores-pruebas", nombre_ajustes="Simuladores Studio pruebas")
piezas = aplicacion.construir(app)
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
ok = app.cargar(aplicacion.QML_DIR / "Main.qml")
raiz = app.motor.rootObjects()[0]
a, m, i = piezas["acciones"], piezas["modelos"], piezas["interfaz"]
banda = raiz.findChild(QObject, "bandaVerificaciones")
m.correr(); app.app.processEvents()
pista = raiz.property("pistaActual")
sin_modelo = banda.property("visible")
m.verificar_al_abrir = False
m.irA("demo/d01"); m.verificar(); app.app.processEvents()
con_modelo = banda.property("visible")
i.pedir.emit("vista", {"indice": 3}); app.app.processEvents(); en_ficha = banda.property("visible")
i.pedir.emit("vista", {"indice": 0}); i.pedir.emit("verificaciones", {}); app.app.processEvents(); oculta = banda.property("visible")
i.pedir.emit("verificaciones", {}); app.app.processEvents(); de_nuevo = banda.property("visible")
accion = a.accion("ver.verificaciones")
ver = next(x for x in a.menus if x["titulo"] == "&Ver")
QTimer.singleShot(300, app.app.quit); app.app.exec(); app.cerrar()
print(json.dumps({"ok": ok, "errores": errores, "pista": pista, "sin_modelo": sin_modelo, "con_modelo": con_modelo, "en_ficha": en_ficha,
                  "oculta": oculta, "de_nuevo": de_nuevo, "atajo": accion.property("atajo"), "en_ver": "ver.verificaciones" in json.dumps(ver),
                  "conflictos": a.conflictos()}))
"""


@requiere_sistema
def test_la_ventana_con_las_verificaciones_al_pie(tmp_path, muestra):
    r = correr_python(VENTANA, entorno_gui(tmp_path, muestra))
    assert r.returncode == 0, r.stderr[-3000:]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos["ok"], r.stderr[-3000:]
    graves = [e for e in datos["errores"] if "TypeError" in e or "ReferenceError" in e or "Cannot assign" in e]
    assert not graves, "\n".join(graves)
    assert datos["pista"] == "Elige primero un modelo."                           # a la barra de estado, no a Plasma
    assert datos["sin_modelo"] is False and datos["con_modelo"] is True
    assert datos["en_ficha"] is False                                             # al pie de las vistas del experimento
    assert datos["oculta"] is False and datos["de_nuevo"] is True                 # Ctrl+Mayús+T
    assert datos["atajo"] in ("Ctrl+Shift+T", "Ctrl+Mayús+T") and datos["en_ver"]
    assert datos["conflictos"] in ({}, [])
