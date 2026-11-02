"""studio/sim_app/aplicacion.py — arma Simuladores Studio: la aplicación (gui_comun.nucleo), los controladores, el
registro de acciones (menú, barra, menú contextual, paleta, atajos) y carga `qml/Main.qml`.

Toda operación existe una sola vez, aquí, en `Acciones`. Las operaciones del catálogo son acciones `op.<id>` que
eligen la operación actual; correrla es siempre F5 (Correr el escenario y Verificar el modelo calculan en proceso con
el motor; lo demás es la CLI del laboratorio o el plan de lo que se escribiría) o Ctrl+Intro (Aplicar, tras confirmar
en QML con la orden exacta y lo que toca). Lo que necesita un diálogo lo pide a QML por `Interfaz.pedir`. Python no
construye interfaz; la ventana no edita ningún modelo.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from gui_comun.acciones import Acciones, StandardKey
from gui_comun.consola import Consola
from gui_comun.nucleo import Aplicacion
from gui_comun.qt import QObject, Signal, Slot
from gui_comun.tareas import Tareas

from sim_app import APP_NAME, APP_VERSION, ORG_NAME
from sim_app.controladores.ajustes import Ajustes
from sim_app.controladores.espacio import Espacio
from sim_app.controladores.modelos import Modelos
from sim_app.controladores.operaciones import Operaciones
from sim_app.servicios import laboratorio as lab
from sim_app.servicios import operaciones as ops
from sim_app.servicios import rutas

APP_DIR = Path(__file__).resolve().parent
QML_DIR = APP_DIR / "qml"
RECURSOS_DIR = APP_DIR / "recursos"
REPO = rutas.REPO
APP_ID = "simuladores-studio"
NOMBRE = APP_NAME
DESCRIPCION = ("El laboratorio computacional en una ventana de trabajo: los modelos de cada disciplina (macroeconomía, estadística) con su "
               "estado de verificación, su ficha pedagógica, sus parámetros y escenarios, la corrida con sus curvas y sus magnitudes frente a "
               "la base, y sus verificaciones numéricas contra la fuente citada. F5 corre el escenario o verifica el modelo con el motor y solo "
               "escribe la caché del studio; Ctrl+Intro exporta figuras y datos, guarda un escenario propio o regenera el catálogo tras "
               "confirmar con la orden exacta. El rigor es del motor: la ventana no edita ningún modelo.")
ACENTO = "lima"


def datos_lanzador() -> dict:
    return dict(app_id=APP_ID, nombre=NOMBRE, comentario="Laboratorio computacional: modelos de economía y estadística que se derivan, simulan y ven",
                orden=[rutas.interprete(), str(APP_DIR.parent / "main.py")], logo_svg=(RECURSOS_DIR / "marca.svg").read_text(encoding="utf-8"),
                acento=ACENTO, categorias="Education;Economy;Math;", palabras="macroeconomía;estadística;simulador;modelo;IS-LM;laboratorio;")


class Interfaz(QObject):
    pedir = Signal(str, "QVariantMap")

    @Slot(str)
    def abrir(self, nombre: str) -> None:
        self.pedir.emit(nombre, {})


def construir(app: Aplicacion, cache: Path | None = None, datos: Path | None = None, raiz: Path | None = None) -> dict:
    """Crea controladores y acciones, y los expone al QML. Devuelve lo creado (para las pruebas y las capturas)."""
    consola = Consola()
    tareas = Tareas(consola)
    interfaz = Interfaz()
    ajustes = Ajustes()
    espacio = Espacio(consola, ajustes)
    modelos = Modelos(espacio, consola, cache=cache, datos=datos, raiz=raiz)
    operaciones = Operaciones(espacio, modelos, ajustes, consola, tareas, cache=cache)
    acciones = Acciones()
    acciones.estandar(NOMBRE)
    pedir = lambda que, **datos_: (lambda *_: interfaz.pedir.emit(que, datos_))
    disciplinas = [d["nombre"] for d in modelos.disciplinas]

    # --- Archivo
    acciones.registrar("archivo.abrir", "&Abrir el archivo del modelo", "document-open", None, "Archivo", habilitada=False,
                       al_disparar=lambda *_: espacio.abrir(modelos.archivo), descripcion="El .py del modelo con la aplicación del sistema (el editor); también Intro en la tabla")
    acciones.registrar("archivo.carpeta", "Abrir su &carpeta", "system-file-manager", "Ctrl+Shift+O", "Archivo", habilitada=False,
                       al_disparar=lambda *_: espacio.abrirDolphin(modelos.archivo or modelos.carpetaDisciplina), descripcion="La carpeta del modelo en Dolphin")
    acciones.registrar("archivo.terminal", "Abrir &terminal en la disciplina", "utilities-terminal", "Shift+F4", "Archivo",
                       al_disparar=lambda *_: espacio.abrirTerminal(modelos.carpetaDisciplina), descripcion="Una terminal en la carpeta de la disciplina (main.py …)")
    acciones.registrar("archivo.copiar", "Copiar la &referencia", "edit-copy", "Ctrl+Shift+C", "Archivo", habilitada=False,
                       al_disparar=lambda *_: espacio.copiar(modelos.ref), descripcion="«disciplina/id», como la citan divulgacion y los cursos")
    acciones.registrar("archivo.catalogo", "Abrir &catalogo.json", "application-json", None, "Archivo",
                       al_disparar=lambda *_: espacio.abrir(str(modelos.raiz / "catalogo.json")))
    # --- Editar
    acciones.registrar("editar.filtrar", "&Filtrar", "edit-find", StandardKey.Find, "Editar", al_disparar=pedir("filtrar"))
    acciones.registrar("editar.todo", "Seleccionar &todo", "edit-select-all", StandardKey.SelectAll, "Editar", al_disparar=pedir("seleccionar_todo"))
    # --- Ver
    acciones.registrar("ver.disciplina", "&Todas las disciplinas", "view-list-tree", "Ctrl+0", "Ver › Disciplina", marcable=True,
                       al_disparar=lambda *_: (espacio.fijarEstado(""), espacio.fijarDisciplina("")))
    for i, d in enumerate(disciplinas, start=1):
        acciones.registrar(f"ver.disciplina.{d}", f"&{i} {lab.nombre_de(d)}", lab.icono_de(d), f"Ctrl+{i}" if i <= 9 else None, "Ver › Disciplina", marcable=True,
                           al_disparar=lambda *_, n=d: (espacio.fijarEstado(""), espacio.fijarDisciplina(n)))
    acciones.registrar("ver.estado", "Todos los &estados", "", None, "Ver › Estado", marcable=True, al_disparar=lambda *_: espacio.fijarEstado(""))
    for e, t in (("verificado", "&Verificados"), ("diferencias", "Con &diferencias"), ("sin_verificar", "&Sin verificar")):
        acciones.registrar(f"ver.estado.{e}", t, "", None, "Ver › Estado", marcable=True, al_disparar=lambda *_, n=e: espacio.fijarEstado(n))
    acciones.registrar("ver.releer", "&Releer el catálogo", "view-refresh", "F6", "Ver", al_disparar=lambda *_: modelos.recargar(),
                       descripcion="Vuelve a leer catalogo.json y los estados de verificación")
    acciones.registrar("ver.figura", "Ver la &figura académica", "office-chart-area", "Ctrl+G", "Ver", marcable=True, marcada=ajustes.figuraAcademica,
                       al_disparar=lambda *_, m=None: figura_academica(), descripcion="La figura de matplotlib (fondo blanco, la paleta del laboratorio) en vez del gráfico en vivo")
    # --- Modelo · Disciplina · Laboratorio: elegir cada operación
    for o in ops.OPERACIONES:
        acciones.registrar(f"op.{o.id}", o.titulo, o.icono, None, dict(ops.GRUPOS)[o.grupo], al_disparar=lambda *_, i=o.id: operaciones.fijar(i), descripcion=o.descripcion)
    acciones.registrar("op.simular", "&Correr", "media-playback-start", StandardKey.Refresh, "Modelo", al_disparar=operaciones.simular,
                       descripcion="Corre la operación elegida: el motor en proceso, la CLI del laboratorio o el plan de lo que se escribiría; la salida queda en el panel inferior")
    acciones.registrar("op.aplicar", "&Aplicar…", "dialog-ok-apply", "Ctrl+Return", "Modelo", habilitada=False, al_disparar=pedir("aplicar"),
                       descripcion="Muestra la orden exacta y lo que toca; si confirmas, escribe de verdad")
    acciones.registrar("op.cancelar", "Ca&ncelar la operación", "process-stop", None, "Modelo", habilitada=False, al_disparar=operaciones.cancelar)
    acciones.registrar("modelo.correr", "Correr el escenario &ahora", "media-playback-start", "Ctrl+R", "Modelo", habilitada=False,
                       al_disparar=lambda *_: (operaciones.fijar("correr"), operaciones.simular()), descripcion="Elige «Correr el escenario» y lo corre")
    acciones.registrar("modelo.verificar", "&Verificar ahora", "checkmark", "Ctrl+T", "Modelo", habilitada=False,
                       al_disparar=lambda *_: (operaciones.fijar("verificar"), operaciones.simular()), descripcion="Elige «Verificar el modelo» y lo verifica")
    acciones.registrar("modelo.restablecer", "&Restablecer los parámetros", "edit-undo", "Ctrl+Shift+R", "Modelo", habilitada=False, al_disparar=lambda *_: modelos.restablecer(),
                       descripcion="Vuelve a los valores por defecto del modelo (la base)")
    acciones.registrar("modelo.recorrido", "Recorrido &guiado…", "media-playlist-play", None, "Modelo", al_disparar=lambda *_: recorrido(),
                       descripcion="La app pedagógica paso a paso de la disciplina (main.py app), en su propia ventana")
    for i, (nombre, texto) in enumerate((("ficha", "Ver la &ficha"), ("escenario", "Ver el &escenario"), ("resultados", "Ver los &resultados"),
                                         ("verificaciones", "Ver las verificaci&ones"))):
        acciones.registrar(f"modelo.{nombre}", texto, "", None, "Modelo", al_disparar=pedir("pestana", indice=i))
    # --- Herramientas
    acciones.registrar("herr.lanzador", "Instalar el acceso &directo", "application-x-executable", None, "Herramientas", al_disparar=lambda *_: instalar_lanzador())
    acciones.registrar("herr.venv", "El &entorno del studio…", "python", None, "Herramientas", al_disparar=pedir("venv"),
                       descripcion="Qué intérprete corre las CLI y la figura académica, y cómo crear el .venv (matplotlib)")
    # --- Ayuda
    acciones.registrar("ayuda.manual", "&Manual de Simuladores Studio", "help-contents", StandardKey.HelpContents, "Ayuda",
                       al_disparar=lambda *_: subprocess.Popen(["xdg-open", str(REPO / "studio" / "README.md")]))
    acciones.registrar("ayuda.disciplina", "&Diseño de la disciplina", "help-hint", None, "Ayuda", al_disparar=lambda *_: abrir_diseno(),
                       descripcion="El documento de diseño de la disciplina del modelo (docs/laboratorio-<disciplina>.md)")

    acciones.definir_menus([
        ("&Archivo", ["archivo.abrir", "archivo.carpeta", "archivo.terminal", "archivo.copiar", "|", "archivo.catalogo", "|", "app.salir"]),
        ("&Editar", ["editar.filtrar", "editar.todo"]),
        ("&Ver", ["ventana.navegacion", "ventana.detalles", "ventana.inferior", "|",
                  ("&Disciplina", ["ver.disciplina"] + [f"ver.disciplina.{d}" for d in disciplinas]),
                  ("&Estado", ["ver.estado", "ver.estado.verificado", "ver.estado.diferencias", "ver.estado.sin_verificar"]), "|",
                  "ver.figura", "ver.releer", "|", "ventana.pantalla_completa"]),
        ("&Modelo", ["op.simular", "op.aplicar", "op.cancelar", "|", "modelo.correr", "modelo.verificar", "modelo.restablecer", "|"]
                    + [f"op.{o.id}" for o in ops.de_grupo("modelo")] + ["|", "modelo.ficha", "modelo.escenario", "modelo.resultados", "modelo.verificaciones", "|", "modelo.recorrido"]),
        ("&Disciplina", [f"op.{o.id}" for o in ops.de_grupo("disciplina")]),
        ("&Laboratorio", [f"op.{o.id}" for o in ops.de_grupo("laboratorio")]),
        ("&Herramientas", ["herr.lanzador", "herr.venv", "|", "ventana.paleta"]),
        ("A&justes", ["app.ajustes"]),
        ("Ay&uda", ["ayuda.manual", "ayuda.disciplina", "app.acerca"]),
    ])
    acciones.definir_barra(["op.simular", "op.aplicar", "|", "modelo.verificar", "modelo.restablecer"])
    acciones.anadir_fuente(espacio.entradas_paleta)
    acciones.anadir_fuente(operaciones.entradas_paleta)
    acciones.anadir_fuente(modelos.entradas_paleta)

    def instalar_lanzador() -> None:
        if not tareas.activa:
            tareas.proceso("Instalando el acceso directo", ["bash", str(REPO / "install.sh")], cwd=str(REPO))

    def recorrido() -> None:
        carpeta = modelos.carpetaDisciplina
        if not (Path(carpeta) / "main.py").is_file():
            interfaz.pedir.emit("aviso", {"texto": "Elige un modelo o una disciplina: el recorrido es de la disciplina (main.py app).", "tipo": "aviso"})
            return
        subprocess.Popen([rutas.interprete(), "main.py", "app"], cwd=carpeta)
        consola.registrar("info", f"Recorrido guiado de {Path(carpeta).name}: se abre en su propia ventana; elige el modelo en su menú.")

    def abrir_diseno() -> None:
        d = modelos.disciplina or espacio.disciplina
        docs = Path(modelos.raiz) / d / "docs" if d else None
        archivo = next(iter(sorted(docs.glob("laboratorio-*.md"))), None) if docs and docs.is_dir() else None
        subprocess.Popen(["xdg-open", str(archivo if archivo else REPO / "README.md")])

    def figura_academica() -> None:
        ajustes.figuraAcademica = acciones.accion("ver.figura").marcada
        if ajustes.figuraAcademica and modelos.hayActual:
            modelos.pedirFigura()

    def filtro_cambiado():
        acciones.marcar("ver.disciplina", espacio.disciplina == "")
        for d in disciplinas:
            acciones.marcar(f"ver.disciplina.{d}", espacio.disciplina == d)
        acciones.marcar("ver.estado", espacio.estado == "")
        for e in ("verificado", "diferencias", "sin_verificar"):
            acciones.marcar(f"ver.estado.{e}", espacio.estado == e)
        disponibilidad()

    def disponibilidad():
        activa = tareas.activa
        hay = modelos.hayActual
        for nombre in ("archivo.abrir", "archivo.carpeta", "archivo.copiar"):
            acciones.habilitar(nombre, hay)
        acciones.habilitar("modelo.correr", hay and modelos.cargado and not activa)
        acciones.habilitar("modelo.verificar", hay and modelos.cargado and not activa)
        acciones.habilitar("modelo.restablecer", hay and modelos.cargado)
        acciones.habilitar("ver.figura", modelos.hayMatplotlib)
        a = acciones.accion("op.simular")
        a.texto = f"&{operaciones.verbo}"
        acciones.habilitar("op.simular", operaciones.puedeSimular)
        b = acciones.accion("op.aplicar")
        b.visible = operaciones.escribe
        acciones.habilitar("op.aplicar", operaciones.puedeAplicar)
        acciones.habilitar("op.cancelar", operaciones.enCurso)
        acciones.habilitar("ver.releer", not activa)
        acciones.habilitar("herr.lanzador", not activa)

    def barra_estado():
        espacio.fijarResumen(modelos.resumen)
        partes = []
        if modelos.hayActual:
            partes.append(f"{modelos.id} · {modelos.textoEstado}" + (f" · escenario {modelos.escenario}" if modelos.cargado else ""))
        if operaciones.hayOperacion:
            partes.append(operaciones.titulo)
        espacio.fijarContexto(" · ".join(partes))

    def figura_si_toca():
        if ajustes.figuraAcademica and modelos.hayActual and modelos.hayMatplotlib:
            modelos.pedirFigura()

    espacio.filtroCambiado.connect(filtro_cambiado)
    modelos.cambiado.connect(lambda: (disponibilidad(), barra_estado()))
    modelos.actualCambiado.connect(lambda: (disponibilidad(), barra_estado(), figura_si_toca()))
    modelos.valoresCambiados.connect(lambda: (disponibilidad(), barra_estado()))
    modelos.corridaCambiada.connect(lambda: (disponibilidad(), figura_si_toca()))
    operaciones.cambiado.connect(lambda: (disponibilidad(), barra_estado()))
    tareas.cambiada.connect(disponibilidad)
    filtro_cambiado()
    barra_estado()

    piezas = dict(consola=consola, tareas=tareas, interfaz=interfaz, ajustes=ajustes, espacio=espacio, modelos=modelos, operaciones=operaciones, acciones=acciones)
    for nombre, objeto in piezas.items():
        app.exponer(nombre, objeto)
    app.exponer("descripcionStudio", DESCRIPCION)
    app._piezas = piezas
    return piezas


def relanzar_con_venv(argv: list[str], guion: Path | None = None) -> None:
    """Si existe el .venv del repo y no es el intérprete actual, relanza `guion` (por omisión main.py) con él (rediseño S9)."""
    venv = rutas.venv_dir() / "bin" / "python"
    ya_dentro = Path(sys.prefix).resolve() == rutas.venv_dir().resolve()      # el ejecutable del .venv es un enlace al del sistema: se mira el prefijo
    if venv.is_file() and not ya_dentro and not os.environ.get(rutas.VARIABLE_SIN_VENV):
        os.execv(str(venv), [str(venv), str(guion or APP_DIR.parent / "main.py"), *argv])


def main(argv: list[str]) -> int:
    relanzar_con_venv(argv)
    if not rutas.hay_venv():
        print(f"{NOMBRE}: sin el entorno del studio no hay matplotlib: la figura académica, las fórmulas, los reportes y las CLI del laboratorio no "
              f"están (correr y verificar un modelo sí). Créalo con:\n  {rutas.orden_crear_venv()}", file=sys.stderr)
    from gui_comun import lanzador
    atendido = lanzador.desde_main(argv, **datos_lanzador())
    if atendido is not None:
        return atendido
    app = Aplicacion(APP_ID, NOMBRE, version=APP_VERSION, organizacion=ORG_NAME, nombre_ajustes=APP_NAME)
    construir(app)
    return app.ejecutar(QML_DIR / "Main.qml", humo="--smoke" in argv)
