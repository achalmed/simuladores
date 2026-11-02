#!/usr/bin/python3
"""studio/capturar.py — una captura de Simuladores Studio para la documentación sobre el LABORATORIO DE MUESTRA
(`muestra.py`: el motor real con una disciplina de juguete, nunca los modelos del repo) creado en una carpeta temporal
fuera de la carpeta de inicio, con HOME, configuración, caché y datos temporales (ninguna ruta de la máquina en
pantalla), el esquema de color que se pida, el modelo, el escenario, los valores de los parámetros, la vista del
espacio de simulación y, si se pide, la paleta.

    /usr/bin/python3 studio/capturar.py docs/figuras/simuladores-studio-oscuro.png --esquema ~/Documents/lliphi/generado/esquema/LliphiOscuro.colors --modelo demo/d01 --escenario 1
    /usr/bin/python3 studio/capturar.py docs/figuras/simuladores-studio-claro.png --esquema ~/Documents/lliphi/generado/esquema/LliphiClaro.colors --modelo demo/d02 --vista 0
    /usr/bin/python3 studio/capturar.py salida.png --modelo demo/d03 --valor s=0.35 --vista 1
    /usr/bin/python3 studio/capturar.py salida.png --paleta "mercado"

Antes de capturar corre de verdad, sobre la muestra, el escenario del modelo elegido y sus verificaciones (el motor
en proceso). El gráfico es un Canvas: la plataforma offscreen lo dibuja con su renderizador (`QT_QUICK_BACKEND=rhi`).
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))


def main() -> int:
    parser = argparse.ArgumentParser(description="Captura de Simuladores Studio sobre el laboratorio de muestra")
    parser.add_argument("salida")
    parser.add_argument("--esquema", help="archivo .colors de KDE (relanza con XDG_CONFIG_HOME temporal)")
    parser.add_argument("--modelo", default="demo/d01", help="la referencia del modelo (disciplina/id; vacío: ninguno)")
    parser.add_argument("--escenario", type=int, default=1, help="el índice del escenario (0 la base)")
    parser.add_argument("--operacion", default="", help="la operación elegida al capturar (id del catálogo)")
    parser.add_argument("--vista", type=int, default=0, help="la vista (0 Simulación · 1 Comparación · 2 Sensibilidad · 3 Ficha · 4 Verificaciones · 5 Laboratorio)")
    parser.add_argument("--valor", action="append", default=[], help="nombre=valor de un parámetro, tras el escenario (se repite)")
    parser.add_argument("--sensibilidad", default="", help="parametro[:magnitud] que barre la vista Sensibilidad")
    parser.add_argument("--sin-correr", action="store_true", help="no corre ni verifica antes de capturar")
    parser.add_argument("--paleta", default=None, help="abre la paleta de órdenes con este texto")
    parser.add_argument("--ancho", type=int, default=1400)
    parser.add_argument("--alto", type=int, default=860)
    args = parser.parse_args()

    if "SIMULADORES_STUDIO_CAPTURA" not in os.environ:      # primera pasada: la muestra, el entorno temporal (y esquema), y relanzar
        from sim_app import aplicacion
        aplicacion.relanzar_con_venv(sys.argv[1:], guion=Path(__file__))   # con el .venv hay fórmulas y figura académica
        from gui_comun.galeria.esquema import entorno_con_esquema
        import muestra
        carpeta = Path(tempfile.mkdtemp(prefix="simuladores-studio-captura-", dir="/tmp"))   # fuera de la carpeta de inicio
        m = muestra.crear(carpeta / "muestra")
        hogar = Path(m.entorno["HOME"])
        config_usuario = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        for nombre in ("kdeglobals", "kcminputrc", "Kvantum", "fontconfig"):
            origen = config_usuario / nombre
            if origen.is_dir():
                shutil.copytree(origen, hogar / ".config" / nombre, dirs_exist_ok=True)
            elif origen.is_file():
                shutil.copy2(origen, hogar / ".config" / nombre)
        env = entorno_con_esquema(Path(args.esquema).expanduser(), hogar / ".config") if args.esquema else dict(os.environ, XDG_CONFIG_HOME=str(hogar / ".config"))
        env.update(m.entorno)
        env.update({"XDG_DATA_HOME": str(Path.home() / ".local" / "share"), "SIMULADORES_STUDIO_CAPTURA": str(carpeta), "QT_QPA_PLATFORM": "offscreen"})
        env.setdefault("QT_QPA_PLATFORMTHEME", "kde")
        env.setdefault("QT_QUICK_BACKEND", "rhi")
        orden = [sys.executable, str(AQUI / "capturar.py")] + [a for a in sys.argv[1:] if not a.startswith("--esquema") and a != args.esquema]
        codigo = subprocess.run(orden, env=env).returncode
        shutil.rmtree(carpeta, ignore_errors=True)
        return codigo

    from sim_app import aplicacion
    from gui_comun.nucleo import Aplicacion
    from gui_comun.qt import QTimer

    app = Aplicacion(aplicacion.APP_ID, aplicacion.NOMBRE, version=aplicacion.APP_VERSION, organizacion=aplicacion.ORG_NAME, nombre_ajustes=aplicacion.APP_NAME)
    piezas = aplicacion.construir(app)
    modelos, operaciones, interfaz = (piezas[k] for k in ("modelos", "operaciones", "interfaz"))
    if not app.cargar(aplicacion.QML_DIR / "Main.qml"):
        return 1
    raiz = app.motor.rootObjects()[0]
    raiz.setProperty("width", args.ancho)
    raiz.setProperty("height", args.alto)

    def listo():
        if args.modelo:
            modelos.irA(args.modelo)
            modelos.aplicarEscenarioPorIndice(args.escenario)
            for par in args.valor:
                nombre, _, valor = par.partition("=")
                modelos.fijarValor(nombre, float(valor))
            if not args.sin_correr:
                operaciones.fijar("verificar")
                operaciones.simular()
                operaciones.fijar("correr")
                operaciones.simular()
            if args.sensibilidad:
                parametro, _, magnitud = args.sensibilidad.partition(":")
                modelos.calcularSensibilidad(parametro, magnitud)
        if args.operacion:
            operaciones.fijar(args.operacion)
        QTimer.singleShot(300, lambda: interfaz.pedir.emit("vista", {"indice": args.vista}))
        if args.paleta is not None:
            QTimer.singleShot(900, lambda: interfaz.pedir.emit("paleta", {"texto": args.paleta}))
        app.capturar(args.salida, espera_ms=2400)

    QTimer.singleShot(400, listo)
    codigo = app.app.exec()
    app.cerrar()
    print("CAPTURA", args.salida)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
