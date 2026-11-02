#!/usr/bin/env bash
# tests/run.sh — corre las pruebas de Simuladores Studio (tests/studio) con pytest, con la carpeta temporal en disco y sin caché.
# Uso: tests/run.sh [opciones de pytest]   (p. ej. -k corridas)
# Las del motor (cada disciplina al 100 %) se corren aparte: `python3 main.py verificar` desde la raíz, como dice CLAUDE.md.
# La carpeta temporal va a ~/.cache (no a /tmp, que es RAM). Nada toca los modelos reales ni catalogo.json: cada prueba
# parte del laboratorio de muestra (studio/muestra.py) en un temporal. Las pruebas en proceso usan el binding del Python
# que corre pytest; las de QML y la de humo abren un proceso hijo con el Python del sistema (/usr/bin/python3, el del Qt
# con Kirigami; el .venv del repo si existe) sin pantalla y con HOME, XDG_CONFIG_HOME y XDG_CACHE_HOME temporales.
set -euo pipefail

DIR_PRUEBAS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/studio"
BASE_TMP="${XDG_CACHE_HOME:-$HOME/.cache}/pytest/simuladores-studio"
mkdir -p "$BASE_TMP"

export PYTHONDONTWRITEBYTECODE=1
export QT_QPA_PLATFORM=offscreen
exec python3 -m pytest "$DIR_PRUEBAS" --basetemp "$BASE_TMP" -p no:cacheprovider -q "$@"
