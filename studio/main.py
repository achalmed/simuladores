#!/usr/bin/env python3
"""
main.py — Punto de entrada de Simuladores Studio.

Orquestación mínima: crea la QApplication, aplica el tema guardado y abre la ventana. La lógica vive en sim_app/ y en
gui_comun (el repo gui-comun); los modelos, en las disciplinas de este repo (macro/, estadistica/…), sin copiarlos.

Uso:
    python3 studio/main.py                    # desde simuladores/
    python3 studio/main.py --smoke            # construye la interfaz y sale (prueba de humo)
    python3 studio/main.py --instalar-lanzador [-n]   # el acceso directo en el menú de aplicaciones
"""

import sys
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI))

import sim_app  # noqa: F401  encuentra gui_comun

APP_ID = "simuladores-studio"


def datos_lanzador() -> dict:
    """El acceso directo en el menú de aplicaciones (gui_comun.lanzador)."""
    from sim_app.ventana import ACENTO, LOGO
    return dict(app_id=APP_ID, nombre="Simuladores Studio", comentario="Laboratorio computacional: modelos de economía "
                "y estadística que se derivan, simulan y ven", orden=[sys.executable, str(_AQUI / "main.py")],
                logo_svg=LOGO, acento=ACENTO, categorias="Education;Economy;Math;",
                palabras="macroeconomía;estadística;simulador;modelo;IS-LM;laboratorio;")


def main() -> int:
    from gui_comun import lanzador
    atendido = lanzador.desde_main(sys.argv[1:], **datos_lanzador())   # --instalar-lanzador / --quitar-lanzador
    if atendido is not None:
        return atendido
    from gui_comun.diseno import preparar_plataforma
    preparar_plataforma()                 # sin el plugin de Wayland, XWayland sin aviso
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    QApplication.setOrganizationName("EdisonAchalma")
    QApplication.setApplicationName("SimuladoresStudio")
    QApplication.setDesktopFileName(APP_ID)    # la ventana se agrupa con su acceso directo (Wayland)
    app = QApplication(sys.argv)
    from sim_app.ventana import Ventana
    ventana = Ventana()
    ventana.show()
    if "--smoke" in sys.argv:
        QTimer.singleShot(0, app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
