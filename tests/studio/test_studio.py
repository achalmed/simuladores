"""tests/studio/test_studio.py — Simuladores Studio (QML + Kirigami sobre gui-comun 2.6) abre su ventana sin pantalla con
el Python del sistema (o el .venv del repo) sobre el laboratorio de muestra: la ventana entera (acciones, menús,
barra, resumen, el modelo elegido, correr y verificar con el motor, el gráfico), cada componente QML, `--smoke`, y
las reglas de la familia (sin colores propios, sin marca dentro, sin QtWidgets, el Python del sistema en main.py e
install.sh; ninguna prueba toca los modelos reales ni catalogo.json)."""
from __future__ import annotations

import json
import re
import subprocess

import pytest

from conftest import PYTHON_SISTEMA, REPO, STUDIO, correr_python, entorno_gui, requiere_sistema

QML = STUDIO / "sim_app" / "qml"

ABRIR = """
import sys, json, os; sys.path.insert(0, sys.argv[1])
from sim_app import aplicacion
from gui_comun.nucleo import Aplicacion
from gui_comun.qt import QTimer
app = Aplicacion("simuladores-studio", "Simuladores Studio", version="prueba", organizacion="simuladores-pruebas", nombre_ajustes="Simuladores Studio pruebas")
piezas = aplicacion.construir(app)
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
ok = app.cargar(aplicacion.QML_DIR / "Main.qml")
raiz = app.motor.rootObjects()[0] if ok else None
a, m, o = piezas["acciones"], piezas["modelos"], piezas["operaciones"]
sin_modelo = (a.accion("op.simular").habilitada, a.accion("modelo.correr").habilitada, a.accion("archivo.abrir").habilitada, a.accion("op.simular").textoPlano)
m.irA("demo/d01"); m.aplicarEscenarioPorIndice(1)
titulo = raiz.property("title") if raiz else ""
con_modelo = (a.accion("op.simular").habilitada, a.accion("modelo.correr").habilitada, a.accion("archivo.abrir").habilitada, a.accion("op.aplicar").visible)
corrio = o.simular()
o.fijar("verificar"); verifico = o.simular()
o.fijar("reporte"); reporte = (a.accion("op.aplicar").visible, a.accion("op.simular").textoPlano, o.puedeAplicar)
QTimer.singleShot(1200, app.app.quit); app.app.exec(); app.cerrar()
print(json.dumps({"ok": ok, "titulo": titulo, "errores": errores, "acciones": a.nombres(), "menus": [x["titulo"] for x in a.menus], "barra": a.barra,
                  "sin_modelo": sin_modelo, "con_modelo": con_modelo, "corrio": corrio, "verifico": verifico, "reporte": reporte, "estado": m.estado,
                  "series": len(m.grafico.get("series", [])), "resumen": piezas["espacio"].resumen, "contexto": piezas["espacio"].contexto, "refs": m.refs}))
"""

COMPONENTE = """
import sys, json, os; sys.path.insert(0, sys.argv[1])
from sim_app import aplicacion
from gui_comun.nucleo import Aplicacion
from gui_comun.qt import QTimer
app = Aplicacion("simuladores-studio", "Simuladores Studio", version="prueba", organizacion="simuladores-pruebas", nombre_ajustes="Simuladores Studio pruebas")
aplicacion.construir(app)
app.motor.addImportPath(str(aplicacion.QML_DIR))
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
nombre, carpeta = sys.argv[2], sys.argv[3]
ruta = os.path.join(os.environ["XDG_CACHE_HOME"], "Prueba_" + nombre + ".qml")
os.makedirs(os.path.dirname(ruta), exist_ok=True)
open(ruta, "w").write('import QtQuick\\nimport GuiComun\\nimport "file://%s/%s"\\nVentanaStudio { id: ventana; acciones: studio.acciones; visible: false; %s { id: objeto } }\\n' % (str(aplicacion.QML_DIR), carpeta, nombre))
ok = app.cargar(ruta)
QTimer.singleShot(400, app.app.quit); app.app.exec(); app.cerrar()
print(json.dumps({"ok": ok, "errores": errores}))
"""


def _graves(errores):
    return [e for e in errores if "TypeError" in e or "ReferenceError" in e or "is not a type" in e or "Cannot assign" in e or "No se puede asignar" in e]


@requiere_sistema
def test_abre_y_cierra_su_ventana(tmp_path, muestra):
    r = correr_python(ABRIR, entorno_gui(tmp_path, muestra))
    assert r.returncode == 0, f"código {r.returncode}\n{r.stderr[-3000:]}"
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos["ok"], r.stderr[-3000:]
    assert not _graves(datos["errores"]), "\n".join(_graves(datos["errores"]))
    assert datos["refs"] == ["demo/d01", "demo/d02"]
    for n in ("archivo.abrir", "archivo.carpeta", "archivo.terminal", "archivo.copiar", "archivo.catalogo", "editar.filtrar", "editar.todo",
              "ver.disciplina", "ver.disciplina.demo", "ver.estado", "ver.estado.verificado", "ver.releer", "ver.figura",
              "op.simular", "op.aplicar", "op.cancelar", "op.correr", "op.verificar", "op.reporte", "op.datos", "op.guardar_escenario", "op.verificar_disciplina", "op.catalogo", "op.web",
              "modelo.correr", "modelo.verificar", "modelo.restablecer", "modelo.recorrido", "modelo.ficha", "herr.lanzador", "herr.venv", "ayuda.manual", "ayuda.disciplina",
              "ventana.navegacion", "ventana.detalles", "ventana.inferior", "ventana.paleta", "app.ajustes", "app.acerca", "app.salir"):
        assert n in datos["acciones"], n
    assert datos["menus"] == ["&Archivo", "&Editar", "&Ver", "&Modelo", "&Disciplina", "&Laboratorio", "&Herramientas", "A&justes", "Ay&uda"]
    assert datos["barra"] == ["op.simular", "op.aplicar", "|", "modelo.verificar", "modelo.restablecer"]
    assert datos["sin_modelo"] == [False, False, False, "Correr"]
    assert datos["con_modelo"] == [True, True, True, False]
    assert datos["corrio"] and datos["verifico"] and datos["estado"] == "verificado" and datos["series"] == 2
    assert datos["reporte"] == [True, "Simular", True]                       # exportar: F5 simula, Ctrl+Intro escribe
    assert datos["resumen"] == "2 modelos · 1 disciplina · 1 verificados · 0 con diferencias · 1 sin verificar"
    assert datos["contexto"].startswith("d01 · Verificado · escenario mas_demanda") and datos["titulo"].startswith("d01 · Mercado lineal")


@requiere_sistema
def test_main_smoke(tmp_path, muestra):
    r = subprocess.run([PYTHON_SISTEMA, str(STUDIO / "main.py"), "--smoke"], env=entorno_gui(tmp_path, muestra), capture_output=True, text=True, timeout=180, cwd=tmp_path)
    assert r.returncode == 0, f"código {r.returncode}\n{r.stderr[-3000:]}"
    ruido = [l for l in r.stderr.splitlines() if "TypeError" in l or "ReferenceError" in l or "polish() loop" in l]
    assert not ruido, "\n".join(ruido)


COMPONENTES = sorted((p.parent.name, p.stem) for p in QML.glob("*/*.qml"))


@requiere_sistema
@pytest.mark.parametrize("carpeta,nombre", COMPONENTES, ids=[f"{c}/{n}" for c, n in COMPONENTES])
def test_cada_componente_qml(carpeta, nombre, tmp_path, muestra):
    r = correr_python(COMPONENTE, entorno_gui(tmp_path, muestra), nombre, carpeta)
    assert r.returncode == 0, r.stderr[-3000:]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos["ok"], r.stderr[-3000:]
    assert not _graves(datos["errores"]), "\n".join(_graves(datos["errores"]))


def test_sin_colores_propios_en_qml():
    malos = []
    for qml in QML.rglob("*.qml"):
        for n, linea in enumerate(qml.read_text(encoding="utf-8").splitlines(), 1):
            sin_comentario = linea.split("//")[0]
            if re.search(r'"#[0-9a-fA-F]{3,8}"', sin_comentario) or re.search(r'\bfont\.(pointSize|pixelSize|family)\s*:\s*["\d]', sin_comentario):
                malos.append(f"{qml.relative_to(STUDIO)}:{n}: {linea.strip()}")
    assert not malos, "\n".join(malos)


def test_sin_marca_dentro_de_la_ventana():
    codigo = "\n".join(l.split("//")[0] for l in (QML / "Main.qml").read_text(encoding="utf-8").splitlines())
    assert "logotipo" not in codigo.lower() and "logo_svg" not in codigo and "marca.svg" not in codigo
    assert 'text: "Simuladores Studio"' not in codigo and "Kirigami.Heading" not in codigo.split("centro:")[0]


def test_sin_qtwidgets_y_con_el_python_del_sistema():
    for py in (STUDIO / "sim_app").rglob("*.py"):
        texto = py.read_text(encoding="utf-8")
        assert "QtWidgets" not in texto and "gui_comun.widgets" not in texto and "gui_comun.diseno" not in texto, py
    assert (STUDIO / "main.py").read_text(encoding="utf-8").startswith("#!/usr/bin/python3")
    instalador = (REPO / "install.sh").read_text(encoding="utf-8")
    assert "/usr/bin/python3" in instalador and ".venv" in instalador
    paquetes = [l.strip() for l in (REPO / "requirements.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    assert not any("pyside" in p.lower() for p in paquetes), paquetes               # el PySide6 es el del sistema
    assert "ninguna prueba toca los modelos reales" in (REPO / "tests" / "studio" / "test_studio.py").read_text(encoding="utf-8")
