#!/usr/bin/python3
"""
main.py — Punto de entrada de Simuladores Studio. Sin lógica: la aplicación se arma en sim_app/aplicacion.py.

Corre con el Python del sistema (/usr/bin/python3), cuyo Qt es el que trae Kirigami; si existe el entorno del studio
(`<repo>/.venv`, creado con `/usr/bin/python3 -m venv --system-site-packages .venv` más `pip install -r requirements.txt`:
matplotlib), se relanza con él: ve el mismo PySide6 del sistema y además lo que el motor necesita para las figuras, las
fórmulas, los reportes y las CLI. Sin el .venv avisa qué crear y sigue (correr y verificar un modelo funcionan igual:
el motor registra un matplotlib vacío, como en el navegador). Los modelos son los de las disciplinas de este repo
(macro/, estadistica/…), sin copiarlos.

Uso:
    /usr/bin/python3 studio/main.py                       # desde simuladores/
    /usr/bin/python3 studio/main.py --smoke               # construye la interfaz y sale (prueba de humo)
    /usr/bin/python3 studio/main.py --instalar-lanzador   # el acceso directo del menú (-n simula)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))      # el paquete del studio

from sim_app.aplicacion import main                             # noqa: E402  (sim_app localiza gui_comun al importarse)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
