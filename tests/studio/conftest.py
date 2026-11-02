"""tests/studio/conftest.py — utilidades de las pruebas de Simuladores Studio (fase 5 QML, 2026-11-02).

El temporal va al disco (XDG_CACHE_HOME), no a /tmp (tmpfs: es RAM). Nada toca los modelos reales ni `catalogo.json`:
cada prueba parte del laboratorio de muestra de `studio/muestra.py` (el motor real con la disciplina `demo` de dos
modelos) en una carpeta temporal, y `SIMULADORES_STUDIO_RAIZ` apunta ahí.

Dos clases de prueba:
- en proceso (servicios, controladores): con el binding del Python que corre pytest; la muestra es una por sesión y la
  raíz se fija antes de importar nada del studio; QSettings apunta a un temporal;
- en un proceso hijo (cada QML, la ventana entera, `--smoke`): con el Python del sistema (/usr/bin/python3; el .venv del
  repo si existe), el único cuyo Qt trae Kirigami, y HOME, XDG_CONFIG_HOME, XDG_CACHE_HOME temporales.

    tests/run.sh            # = python3 -m pytest tests/studio --basetemp ~/.cache/pytest/simuladores-studio -p no:cacheprovider
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
STUDIO = REPO / "studio"
BASETEMP = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "pytest" / "simuladores-studio" / "basetemp"

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if str(STUDIO) not in sys.path:
    sys.path.insert(0, str(STUDIO))

import muestra as muestra_mod  # noqa: E402

HAY_BINDING = importlib.util.find_spec("PySide6") is not None or importlib.util.find_spec("PyQt6") is not None
HAY_MATPLOTLIB = importlib.util.find_spec("matplotlib") is not None
requiere_binding = pytest.mark.skipif(not HAY_BINDING, reason="sin PySide6 ni PyQt6")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    if config.option.basetemp:
        return
    args = [Path(a.split("::")[0]).resolve() for a in (config.args or [])]
    if args and all(REPO in a.parents or a == REPO for a in args):
        BASETEMP.parent.mkdir(parents=True, exist_ok=True)
        config.option.basetemp = str(BASETEMP)


def _python_del_sistema() -> str | None:
    venv = REPO / ".venv" / "bin" / "python"
    for candidato in (venv, Path("/usr/bin/python3")):
        if not candidato.is_file():
            continue
        r = subprocess.run([str(candidato), "-c", "import importlib.util as u; print(bool(u.find_spec('PySide6') or u.find_spec('PyQt6')))"],
                           capture_output=True, text=True)
        if r.stdout.strip() == "True":
            return str(candidato)
    return None


PYTHON_SISTEMA = _python_del_sistema()
requiere_sistema = pytest.mark.skipif(PYTHON_SISTEMA is None, reason="sin binding de Qt en /usr/bin/python3 (Kirigami)")


def _hay_matplotlib_en(python: str | None) -> bool:
    if python is None:
        return False
    r = subprocess.run([python, "-c", "import importlib.util as u; s=u.find_spec('matplotlib'); print(bool(s and s.origin))"], capture_output=True, text=True)
    return r.stdout.strip() == "True"


MATPLOTLIB_SISTEMA = _hay_matplotlib_en(PYTHON_SISTEMA)
requiere_matplotlib = pytest.mark.skipif(not MATPLOTLIB_SISTEMA, reason="sin matplotlib en el Python del studio (crea el .venv)")


@pytest.fixture(scope="session")
def muestra_sesion(tmp_path_factory):
    """El laboratorio de muestra de las pruebas en proceso: uno por sesión; la raíz se fija antes de importar el studio."""
    m = muestra_mod.crear(tmp_path_factory.mktemp("muestra") / "laboratorio")
    os.environ["SIMULADORES_STUDIO_RAIZ"] = str(m.raiz)
    os.environ["MPLBACKEND"] = "Agg"
    return m


@pytest.fixture
def muestra(tmp_path):
    """Un laboratorio de muestra nuevo por prueba (para los procesos hijos y para lo que escribe)."""
    return muestra_mod.crear(tmp_path / "laboratorio")


@pytest.fixture
def ajustes_temporales(tmp_path, monkeypatch):
    from gui_comun.qt import QSettings
    QSettings.setPath(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    return tmp_path


def entorno_gui(tmp_path: Path, muestra, **extra: str) -> dict:
    env = dict(os.environ)
    env.update({"QT_QPA_PLATFORM": "offscreen", "PYTHONDONTWRITEBYTECODE": "1"})
    env.update(muestra.entorno)
    env.pop("SIMULADORES_STUDIO_SIN_VENV", None)
    env.update(extra)
    return env


def correr_python(guion: str, env: dict, *args: str, plazo: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run([PYTHON_SISTEMA or sys.executable, "-c", guion, str(STUDIO), *args], env=env, capture_output=True, text=True, timeout=plazo)


@pytest.fixture(scope="session")
def app(muestra_sesion):
    from gui_comun.qt import QGuiApplication
    QGuiApplication.setOrganizationName("simuladores-studio-pruebas")
    QGuiApplication.setApplicationName("simuladores-studio-pruebas")
    instancia = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    yield instancia
