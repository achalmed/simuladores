"""tests/test_studio.py — Simuladores Studio (2026-10-31): el laboratorio cambia de disciplina sin mezclarlas y la
ventana abre cada modelo del catálogo con su gráfico. Se corre desde la raíz: python3 -m pytest -q tests
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "studio"))

from sim_app.laboratorio import Laboratorio, catalogo  # noqa: E402


def test_cambia_de_disciplina_sin_mezclarlas():
    lab = Laboratorio()
    m = lab.modelo("macro", "m03")
    assert sys.modules["config"].AREA == "macroeconomia"
    e = lab.modelo("estadistica", "e02")
    assert sys.modules["config"].AREA == "estadistica-econometria"
    assert lab.modelo("macro", "m03") is m and sys.modules["config"].AREA == "macroeconomia"
    assert e.ficha and m.curvas(m.dict_params())


def test_cada_modelo_del_catalogo_se_carga():
    lab = Laboratorio()
    c = catalogo()
    for f in c["modelos"]:
        assert lab.modelo(f["disciplina"], f["id"]) is not None, f["ref"]


@pytest.fixture(scope="module")
def app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import sim_app  # noqa: F401
    from PySide6.QtWidgets import QApplication
    QApplication.setOrganizationName("simuladores-pruebas")
    QApplication.setApplicationName("simuladores-studio-pruebas")
    return QApplication.instance() or QApplication([])


def test_la_ventana_abre_modelos_de_las_dos_disciplinas(app):
    from sim_app.ventana import Ventana
    v = Ventana()
    v.show()
    for id_ in ("m10", "e02"):
        f = next(x for x in v.cat["modelos"] if x["id"] == id_)
        v.abrir_modelo(f["disciplina"], f)
        p = v._modelos[f"{f['disciplina']}/{id_}"]
        assert v.ui.stack.currentWidget() is p
        p._dibujar()
        assert p.ejes.has_data()
        if p.m.escenarios:
            p._escenario(p.m.escenarios[0])
    v.ui.close()


def test_main_smoke(tmp_path):
    entorno = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "XDG_CONFIG_HOME": str(tmp_path)}
    r = subprocess.run([sys.executable, str(RAIZ / "studio" / "main.py"), "--smoke"], env=entorno, cwd=tmp_path,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
