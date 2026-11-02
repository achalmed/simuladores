#!/usr/bin/env bash
# install.sh — instala Simuladores Studio: su acceso directo en el menú de aplicaciones, con su icono (gui_comun.lanzador).
# Corre con el Python del studio: el .venv del repo si existe (creado con /usr/bin/python3 -m venv --system-site-packages
# .venv; ve el PySide6 y el Kirigami del sistema y añade matplotlib) o, si no, /usr/bin/python3.
# Uso: ./install.sh [-n]        instala (con -n, solo dice qué escribiría)
#      ./install.sh --quitar    quita el acceso directo y su icono
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -x "$DIR/.venv/bin/python" ]]; then
    PYTHON="${PYTHON:-$DIR/.venv/bin/python}"
else
    PYTHON="${PYTHON:-/usr/bin/python3}"
fi
if [[ "${1:-}" == "--quitar" ]]; then
    shift
    exec "$PYTHON" "$DIR/studio/main.py" --quitar-lanzador "$@"
fi
exec "$PYTHON" "$DIR/studio/main.py" --instalar-lanzador "$@"
