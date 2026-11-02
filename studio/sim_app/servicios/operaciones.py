"""studio/sim_app/servicios/operaciones.py — el catálogo de operaciones de Simuladores Studio (sin Qt): lo que
F5 corre o lee y lo que Ctrl+Intro escribe tras confirmar. Cada operación existe una sola vez aquí; `aplicacion.py` la
registra como acción y `controladores/operaciones.py` la corre: en proceso (`en_proceso`: correr el escenario, verificar
el modelo, guardar el escenario, escribir los datos) o como la CLI del laboratorio (`simular`/`aplicar` devuelven la
orden) con `gui_comun.tareas.proceso`. Las CLI corren con el intérprete del studio (el .venv del repo: matplotlib)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sim_app.servicios import rutas

GRUPOS = (("modelo", "Modelo"), ("disciplina", "Disciplina"), ("laboratorio", "Laboratorio"))


@dataclass
class Contexto:
    raiz: Path
    disciplina: str = ""
    id: str = ""
    escenario: str = ""
    parametro: str = ""
    escenarios: list = field(default_factory=list)
    valor: str = ""                       # lo que la operación pide (texto)


@dataclass
class Orden:
    argv: list
    cwd: Path

    def texto(self) -> str:
        """La orden como se escribiría en la terminal, con rutas relativas a la raíz del laboratorio."""
        partes = []
        for a in self.argv:
            partes.append(rutas.relativa(a) if str(a).startswith("/") else str(a))
        cd = rutas.relativa(self.cwd)
        return (f"cd {cd} && " if cd and cd != "." else "") + " ".join(partes)


@dataclass
class Operacion:
    id: str
    titulo: str
    descripcion: str
    grupo: str                                  # modelo · disciplina · laboratorio
    en_proceso: str = ""                        # correr · verificar · guardar · datos · plan: lo hace la ventana con el motor
    simular: object = None                      # f(ctx) -> Orden (F5)
    aplicar: object = None                      # f(ctx) -> Orden (Ctrl+Intro, tras confirmar)
    escribe: bool = False
    toca: str = "solo lee"
    sobre_modelo: bool = False
    sobre_disciplina: bool = False
    entrada: str = ""                           # "parametro" · "escenarios" · "nombre": lo que pide
    etiqueta: str = ""
    icono: str = "system-run"

    @property
    def verbo(self) -> str:
        if self.en_proceso == "correr":
            return "Correr"
        if self.en_proceso == "verificar":
            return "Verificar"
        if self.escribe:
            return "Simular"
        return "Ejecutar"


def _main_disciplina(ctx: Contexto, *args: str) -> Orden:
    return Orden(["python3", "main.py", *args], ctx.raiz / ctx.disciplina)


def _main_raiz(ctx: Contexto, *args: str) -> Orden:
    return Orden(["python3", "main.py", *args], ctx.raiz)


OPERACIONES: tuple[Operacion, ...] = (
    # --- el modelo
    Operacion("correr", "Correr el escenario", "Calcula las curvas y los resultados del modelo con los valores del escenario (el motor, en proceso) y los deja en Resultados; la corrida queda en la caché del studio",
              "modelo", en_proceso="correr", sobre_modelo=True, icono="media-playback-start"),
    Operacion("verificar", "Verificar el modelo", "Corre las verificaciones numéricas del modelo (la coherencia estructural, sus identidades y teoremas) y comprueba sus citas; el estado del modelo se actualiza",
              "modelo", en_proceso="verificar", sobre_modelo=True, icono="checkmark"),
    Operacion("sensibilidad", "Sensibilidad a un parámetro", "∂magnitud/∂parámetro y la tabla en malla sobre el rango del parámetro (main.py sensibilidad)",
              "modelo", simular=lambda c: _main_disciplina(c, "sensibilidad", c.id, "--param", c.valor or c.parametro), sobre_modelo=True,
              entrada="parametro", etiqueta="Parámetro", icono="office-chart-line-stacked"),
    Operacion("comparar", "Comparar los escenarios", "La tabla de comparación de los escenarios del modelo frente a la base (main.py comparar)",
              "modelo", simular=lambda c: _main_disciplina(c, "comparar", c.id, *(c.escenarios or ["base"])), sobre_modelo=True, icono="view-list-details"),
    Operacion("ficha_cli", "Ficha en la terminal", "La ficha pedagógica tal como la imprime la CLI (main.py ficha)",
              "modelo", simular=lambda c: _main_disciplina(c, "ficha", c.id), sobre_modelo=True, icono="text-x-generic"),
    Operacion("reporte", "Exportar el reporte y las figuras", "Escribe el informe Markdown y las láminas PNG del modelo en salidas/ de su disciplina (main.py reporte)",
              "modelo", simular=lambda c: _main_disciplina(c, "ficha", c.id), aplicar=lambda c: _main_disciplina(c, "reporte", c.id), escribe=True,
              toca="escribe salidas/nivel_NN/<id>_<slug>/ de la disciplina (reporte.md y las figuras; regenerable, fuera de git)", sobre_modelo=True, icono="document-export"),
    Operacion("datos", "Exportar los datos del escenario", "Escribe las series de la corrida (CSV) y la corrida entera (JSON) en salidas/ de la disciplina; F5 muestra qué escribiría",
              "modelo", en_proceso="datos", escribe=True, toca="escribe salidas/studio/<id>/<escenario>.csv y .json de la disciplina (regenerable, fuera de git)",
              sobre_modelo=True, icono="x-office-spreadsheet"),
    Operacion("guardar_escenario", "Guardar el escenario propio", "Guarda los valores actuales de los parámetros como un escenario propio del studio (no toca el modelo); F5 muestra qué guardaría",
              "modelo", en_proceso="guardar", escribe=True, toca="escribe un escenario propio en los datos del studio ($XDG_DATA_HOME/simuladores-studio/escenarios/); el modelo no cambia",
              sobre_modelo=True, entrada="nombre", etiqueta="Nombre del escenario", icono="document-save"),
    # --- la disciplina
    Operacion("verificar_disciplina", "Verificar la disciplina", "main.py verificar de la disciplina: todas las verificaciones de todos sus modelos; los estados de la tabla se actualizan con su salida",
              "disciplina", simular=lambda c: _main_disciplina(c, "verificar"), sobre_disciplina=True, icono="checkmark"),
    Operacion("fuentes", "Comprobar las citas", "main.py fuentes de la disciplina: cada cita contra la hoja del PDF de la biblioteca (estadística)",
              "disciplina", simular=lambda c: _main_disciplina(c, "fuentes"), sobre_disciplina=True, icono="bookmarks"),
    Operacion("listar", "Listar los modelos", "main.py listar de la disciplina: los modelos por sección",
              "disciplina", simular=lambda c: _main_disciplina(c, "listar"), sobre_disciplina=True, icono="view-list-text"),
    # --- el laboratorio
    Operacion("catalogo", "Regenerar el catálogo", "catalogo.json, el contrato de los pubs: F5 comprueba si está al día (--verificar); Ctrl+Intro lo reescribe (--aplicar)",
              "laboratorio", simular=lambda c: _main_raiz(c, "catalogo", "--verificar"), aplicar=lambda c: _main_raiz(c, "catalogo", "--aplicar"), escribe=True,
              toca="reescribe catalogo.json en la raíz del laboratorio (lo consumen los pubs y divulgacion)", icono="view-refresh"),
    Operacion("web", "Regenerar el navegador", "navegador.json, lo que corre en el navegador con Pyodide: F5 comprueba si está al día (--verificar); Ctrl+Intro lo reescribe (--aplicar)",
              "laboratorio", simular=lambda c: _main_raiz(c, "web", "--verificar"), aplicar=lambda c: _main_raiz(c, "web", "--aplicar"), escribe=True,
              toca="reescribe navegador.json en la raíz del laboratorio", icono="internet-web-browser"),
    Operacion("verificar_todo", "Verificar todo el laboratorio", "main.py verificar de la raíz: cada disciplina al 100 %",
              "laboratorio", simular=lambda c: _main_raiz(c, "verificar"), icono="checkmark"),
)


def operacion(id_: str) -> Operacion | None:
    return next((o for o in OPERACIONES if o.id == id_), None)


def de_grupo(grupo: str) -> list[Operacion]:
    return [o for o in OPERACIONES if o.grupo == grupo]
