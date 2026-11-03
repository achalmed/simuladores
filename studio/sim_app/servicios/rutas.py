"""studio/sim_app/servicios/rutas.py — dónde está cada cosa: la raíz del laboratorio (el repo, o la que diga
`SIMULADORES_STUDIO_RAIZ`: el laboratorio de muestra de las pruebas y las capturas), el `.venv` del repo y el
intérprete con el que corren las CLI de las disciplinas, por `core/env.py` cuando el espacio de trabajo está
(`gui_comun.rutas`). Ninguna ruta de la máquina aquí."""
from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]          # simuladores (studio/sim_app/servicios/rutas.py)
VARIABLE_RAIZ = "SIMULADORES_STUDIO_RAIZ"
VARIABLE_SIN_VENV = "SIMULADORES_STUDIO_SIN_VENV"
PAQUETES_VENV = "matplotlib"                        # lo que el motor necesita y el Python del sistema no trae (requirements.txt)


def raiz() -> Path:
    """La raíz del laboratorio: el repo, salvo que `SIMULADORES_STUDIO_RAIZ` apunte a otro (la muestra)."""
    otra = os.environ.get(VARIABLE_RAIZ, "").strip()
    return Path(otra).expanduser().resolve() if otra else REPO


def core_env():
    """El módulo core/env.py del espacio de trabajo, o None fuera de él (el studio corre igual)."""
    try:
        from gui_comun import rutas
        return rutas.core_env()
    except Exception:       # noqa: BLE001  sin core/ el repo se basta
        return None


def venv_dir() -> Path:
    """El entorno del studio (`<repo>/.venv`, creado con `/usr/bin/python3 -m venv --system-site-packages`): ahí vive
    `matplotlib` (las figuras académicas, los reportes y las CLI de las disciplinas), que el Python del sistema no trae."""
    return REPO / ".venv"


def hay_venv() -> bool:
    return (venv_dir() / "bin" / "python").is_file()


def interprete() -> str:
    """El Python con el que corren las CLI del laboratorio: el del `.venv` si existe; si no, `CORE_PYTHON` de
    `core/env.py` (o /usr/bin/python3). Sin `matplotlib` las CLI fallan y la ventana dice qué crear."""
    candidato = venv_dir() / "bin" / "python"
    if candidato.is_file():
        return str(candidato)
    env = core_env()
    return str(getattr(env, "CORE_PYTHON", "/usr/bin/python3")) if env is not None else "/usr/bin/python3"


def orden_crear_venv() -> str:
    """La orden que crea el entorno del studio (se muestra, no se corre sola)."""
    return f"/usr/bin/python3 -m venv --system-site-packages {venv_dir()} && {venv_dir()}/bin/pip install -r {REPO / 'requirements.txt'}"


def hay_matplotlib() -> bool:
    """¿El intérprete actual trae matplotlib de verdad (no el vacío que registra navegador.py)? Con el vacío ya en
    `sys.modules`, `find_spec` no se puede llamar (su `__spec__` es None: ValueError): se mira su origen."""
    import importlib.util
    import sys
    cargado = sys.modules.get("matplotlib")
    if cargado is not None:
        spec = getattr(cargado, "__spec__", None)
        return spec is not None and spec.origin is not None
    try:
        spec = importlib.util.find_spec("matplotlib")
    except (ValueError, ImportError):
        return False
    return spec is not None and spec.origin is not None


def relativa(ruta: Path | str) -> str:
    """Una ruta relativa a la raíz del laboratorio cuando cae dentro (para mostrarla sin la ruta de la máquina)."""
    ruta = Path(ruta)
    try:
        return ruta.relative_to(raiz()).as_posix()
    except ValueError:
        return str(ruta)
