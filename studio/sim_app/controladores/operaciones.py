"""studio/sim_app/controladores/operaciones.py — la operación actual (del catálogo `servicios.operaciones`): lo que pide,
Simular/Correr/Verificar (F5: en proceso con el motor, o la CLI del laboratorio en simulación o solo lectura) y
Aplicar (Ctrl+Intro, tras confirmar en QML con la orden exacta y lo que toca) por `gui_comun.tareas.proceso` (una a
la vez; la salida íntegra en el panel inferior; Esc cancela); el plan (la última simulación) y el registro (la última
aplicación) por operación en la caché del studio. Al terminar `main.py verificar` de una disciplina, su salida
actualiza el estado de todos sus modelos."""
from __future__ import annotations

import time
from pathlib import Path

from gui_comun.qt import QObject, QSettings, Property, Signal, Slot

from sim_app.servicios import operaciones as ops
from sim_app.servicios import rutas


class Operaciones(QObject):
    cambiado = Signal()
    corridaCambiada = Signal()
    terminada = Signal(str, bool, int)      # id, aplicar, código
    aviso = Signal(str, str)

    def __init__(self, espacio, modelos, ajustes, consola, tareas, cache: Path | None = None, parent=None):
        super().__init__(parent)
        self.espacio, self.modelos, self.ajustes, self.consola, self.tareas = espacio, modelos, ajustes, consola, tareas
        self._s = QSettings()
        self._cache = (cache or modelos._cache) / "operaciones"
        guardada = str(self._s.value("operacion/actual", "correr") or "correr")
        self._actual = guardada if ops.operacion(guardada) else "correr"
        self._worker = None
        self._id_en_curso = ""
        self._disciplina_en_curso = ""
        self._aplicando = False
        self._lineas: list[str] = []
        self._inicio = 0.0
        self._argv: list[str] = []
        modelos.actualCambiado.connect(self.cambiado)
        modelos.valoresCambiados.connect(self.cambiado)
        modelos.corridaCambiada.connect(self.cambiado)
        espacio.filtroCambiado.connect(self.cambiado)
        tareas.cambiada.connect(self.cambiado)
        tareas.linea.connect(self._linea)

    # ------------------------------------------------------------ la operación actual
    def _op(self) -> ops.Operacion | None:
        return ops.operacion(self._actual)

    @Property("QVariantList", constant=True)
    def lista(self) -> list:
        grupos = dict(ops.GRUPOS)
        return [{"id": o.id, "titulo": o.titulo, "descripcion": o.descripcion, "grupo": grupos[o.grupo], "icono": o.icono} for o in ops.OPERACIONES]

    @Property(int, notify=cambiado)
    def indiceActual(self) -> int:
        return next((i for i, o in enumerate(ops.OPERACIONES) if o.id == self._actual), -1)

    @Slot(int)
    def fijarPorIndice(self, i: int) -> None:
        if 0 <= i < len(ops.OPERACIONES):
            self.fijar(ops.OPERACIONES[i].id)

    @Slot(str)
    def fijar(self, id_: str) -> None:
        if ops.operacion(id_) is None:
            return
        if id_ != self._actual:
            self._actual = id_
            self._s.setValue("operacion/actual", id_)
        self.cambiado.emit()
        self.corridaCambiada.emit()

    @Property(bool, notify=cambiado)
    def hayOperacion(self) -> bool:
        return self._op() is not None

    @Property(str, notify=cambiado)
    def actual(self) -> str:
        return self._actual

    @Property(str, notify=cambiado)
    def titulo(self) -> str:
        o = self._op()
        return o.titulo if o else ""

    @Property(str, notify=cambiado)
    def descripcion(self) -> str:
        o = self._op()
        return o.descripcion if o else ""

    @Property(str, notify=cambiado)
    def verbo(self) -> str:
        o = self._op()
        return o.verbo if o else "Simular"

    @Property(bool, notify=cambiado)
    def escribe(self) -> bool:
        o = self._op()
        return bool(o and o.escribe)

    @Property(bool, notify=cambiado)
    def enProceso(self) -> bool:
        o = self._op()
        return bool(o and o.en_proceso)

    @Property(bool, notify=cambiado)
    def sobreModelo(self) -> bool:
        o = self._op()
        return bool(o and o.sobre_modelo)

    @Property(bool, notify=cambiado)
    def sobreDisciplina(self) -> bool:
        o = self._op()
        return bool(o and o.sobre_disciplina)

    @Property(str, notify=cambiado)
    def queToca(self) -> str:
        o = self._op()
        if o is None:
            return ""
        if o.en_proceso == "correr":
            return "solo lee: calcula en proceso y guarda la corrida en la caché del studio"
        if o.en_proceso == "verificar":
            return "solo lee: corre las verificaciones en proceso y guarda el estado en la caché del studio"
        return o.toca

    @Property(str, notify=cambiado)
    def grupo(self) -> str:
        o = self._op()
        return dict(ops.GRUPOS)[o.grupo] if o else ""

    # ------------------------------------------------------------------ lo que pide
    @Property(str, notify=cambiado)
    def entradaTipo(self) -> str:
        o = self._op()
        return o.entrada if o else ""

    @Property(str, notify=cambiado)
    def entradaEtiqueta(self) -> str:
        o = self._op()
        return o.etiqueta if o else ""

    def _valor_de(self, o: ops.Operacion) -> str:
        guardado = str(self._s.value(f"entrada/{o.id}/{self.modelos.ref}", "") or "")
        if guardado:
            return guardado
        if o.entrada == "parametro":
            p = self.modelos.parametros
            return p[0]["nombre"] if p else ""
        return ""

    @Property(str, notify=cambiado)
    def valor(self) -> str:
        o = self._op()
        return self._valor_de(o) if o and o.entrada else ""

    @Slot(str)
    def fijarValor(self, v: str) -> None:
        o = self._op()
        if o and o.entrada and v != self._valor_de(o):
            self._s.setValue(f"entrada/{o.id}/{self.modelos.ref}", v)
            self.cambiado.emit()

    @Property("QVariantList", notify=cambiado)
    def nombresParametros(self) -> list:
        return [p["nombre"] for p in self.modelos.parametros]

    # ------------------------------------------------------------------ la disciplina sobre la que corre
    def _disciplina(self) -> str:
        """La del modelo actual; si no hay modelo, la del filtro de la navegación."""
        return self.modelos.disciplina or self.espacio.disciplina

    @Property(str, notify=cambiado)
    def disciplina(self) -> str:
        return self._disciplina()

    def contexto(self) -> ops.Contexto:
        o = self._op()
        m = self.modelos
        return ops.Contexto(raiz=m.raiz, disciplina=self._disciplina(), id=m.id, escenario=m.escenario, parametro=self._valor_de(o) if o and o.entrada == "parametro" else "",
                            escenarios=list(m.nombresEscenarios), valor=self._valor_de(o) if o and o.entrada else "")

    @Property(str, notify=cambiado)
    def ordenSimular(self) -> str:
        o = self._op()
        if o is None:
            return ""
        if o.en_proceso:
            return {"correr": "(el motor en proceso: navegador.calcular con los valores del escenario)", "verificar": "(el motor en proceso: base.verificar y fuentes.comprobar)",
                    "guardar": "(muestra qué guardaría)", "datos": "(muestra qué escribiría)"}.get(o.en_proceso, "")
        try:
            return o.simular(self.contexto()).texto()
        except Exception as e:      # noqa: BLE001
            return f"(no se puede armar la orden: {e})"

    @Property(str, notify=cambiado)
    def ordenAplicar(self) -> str:
        o = self._op()
        if o is None or not o.escribe:
            return ""
        if o.en_proceso == "guardar":
            return "(escribe el escenario propio en los datos del studio)"
        if o.en_proceso == "datos":
            return "(escribe el CSV y el JSON de la corrida en salidas/ de la disciplina)"
        try:
            return o.aplicar(self.contexto()).texto()
        except Exception as e:      # noqa: BLE001
            return f"(no se puede armar la orden: {e})"

    # ----------------------------------------------------------- disponibilidad
    @Property(bool, notify=cambiado)
    def enCurso(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    @Property(str, notify=cambiado)
    def motivoNoSimular(self) -> str:
        o = self._op()
        if o is None:
            return "No hay operación elegida."
        if self.tareas.activa:
            return "Hay una operación en curso (Esc la cancela)."
        if o.sobre_modelo and not self.modelos.hayActual:
            return "Elige primero un modelo en la tabla."
        if o.sobre_modelo and o.en_proceso and not self.modelos.cargado:
            return "El modelo no se pudo importar: " + self.modelos.motivoNoCargado
        if o.sobre_disciplina and not self._disciplina():
            return "Elige una disciplina en la navegación o un modelo en la tabla."
        if o.id == "fuentes" and self._disciplina() and not (self.modelos.raiz / self._disciplina() / "docs").is_dir() and self._disciplina() != "estadistica":
            pass
        if o.entrada == "parametro" and not self._valor_de(o).strip():
            return "Elige el parámetro (pestaña Operación)."
        if o.id in ("datos",) and not self.modelos.hayCorrida:
            return "No hay corrida: corre primero el escenario."
        if not o.en_proceso and not rutas.hay_venv() and not rutas.hay_matplotlib():
            return "Las CLI del laboratorio necesitan matplotlib: crea el .venv del repo (Herramientas › El entorno del studio…)."
        return ""

    @Property(bool, notify=cambiado)
    def puedeSimular(self) -> bool:
        return self.motivoNoSimular == ""

    @Property(str, notify=cambiado)
    def motivoNoAplicar(self) -> str:
        o = self._op()
        if o is None or not o.escribe:
            return "Esta operación no tiene modo «aplicar»: con F5 se ejecuta."
        return self.motivoNoSimular

    @Property(bool, notify=cambiado)
    def puedeAplicar(self) -> bool:
        return self.motivoNoAplicar == ""

    @Property(str, notify=cambiado)
    def textoConfirmacion(self) -> str:
        o = self._op()
        if o is None:
            return ""
        lineas = [f"Orden: {self.ordenAplicar}", "", f"Esta operación {self.queToca}."]
        if o.sobre_modelo and self.modelos.hayActual:
            lineas.append(f"Modelo: {self.modelos.ref} · escenario {self.modelos.escenario}.")
        if o.grupo == "laboratorio":
            lineas.append("Sobre todo el laboratorio.")
        return "\n".join(lineas)

    # ------------------------------------------------------------------ correr
    @Slot(result=bool)
    def simular(self) -> bool:
        """F5: correr o verificar en proceso, el plan de lo que escribe, o la CLI del laboratorio."""
        o = self._op()
        if o is None or not self.puedeSimular:
            self.aviso.emit(self.motivoNoSimular, "aviso")
            return False
        inicio = time.monotonic()
        if o.en_proceso == "correr":
            ok = self.modelos.correr()
            if ok:
                self._escribir(o.id, False, self.modelos.registro)
                self.aviso.emit(f"{self.modelos.id} · {self.modelos.escenario} corrido en {(time.monotonic() - inicio) * 1000:.0f} ms: Resultados.", "informacion")
            self.corridaCambiada.emit()
            self.terminada.emit(o.id, False, 0 if ok else 1)
            return ok
        if o.en_proceso == "verificar":
            ok = self.modelos.verificar()
            n, fallos = self.modelos.nVerificaciones, self.modelos.nFallos
            self._escribir(o.id, False, f"# {time.strftime('%Y-%m-%d %H:%M:%S')} · verificar · {self.modelos.ref}\n{n - fallos}/{n} superadas\n")
            self.aviso.emit(f"{self.modelos.id}: {n - fallos} de {n} verificaciones superadas." + ("" if ok else " Mira Verificaciones."), "positivo" if ok else "error")
            self.corridaCambiada.emit()
            self.terminada.emit(o.id, False, 0 if ok else 1)
            return ok
        if o.en_proceso in ("guardar", "datos"):
            texto = self.modelos.planGuardarEscenario(self._valor_de(o)) if o.en_proceso == "guardar" else self.modelos.planDatos()
            self._escribir(o.id, False, f"# {time.strftime('%Y-%m-%d %H:%M:%S')} · plan · {o.titulo}\n\n{texto}\n")
            for linea in texto.splitlines():
                self.consola.escribir(linea, "info")
            self.aviso.emit(f"Plan de «{o.titulo}» en la pestaña Operación: revísalo y aplica con Ctrl+Intro.", "informacion")
            self.corridaCambiada.emit()
            return True
        return self._lanzar(o, o.simular(self.contexto()), aplicar=False)

    @Slot(result=bool)
    def aplicar(self) -> bool:
        """Ctrl+Intro, tras la confirmación en QML."""
        o = self._op()
        if o is None or not self.puedeAplicar:
            self.aviso.emit(self.motivoNoAplicar, "aviso")
            return False
        if o.en_proceso == "guardar":
            ok = self.modelos.guardarEscenario(self._valor_de(o))
            self._escribir(o.id, True, f"# {time.strftime('%Y-%m-%d %H:%M:%S')} · aplicado · {o.titulo}\n{self.modelos.ref} · {self.modelos.escenario}\n")
            if ok:
                self.aviso.emit(f"Escenario «{self.modelos.escenario}» guardado en los datos del studio.", "positivo")
            self.corridaCambiada.emit()
            self.terminada.emit(o.id, True, 0 if ok else 1)
            return ok
        if o.en_proceso == "datos":
            ok = self.modelos.escribirDatos()
            self._escribir(o.id, True, f"# {time.strftime('%Y-%m-%d %H:%M:%S')} · aplicado · {o.titulo}\n{self.modelos.planDatos()}\n")
            if ok:
                self.aviso.emit("Datos del escenario escritos en salidas/ de la disciplina.", "positivo")
            self.corridaCambiada.emit()
            self.terminada.emit(o.id, True, 0 if ok else 1)
            return ok
        return self._lanzar(o, o.aplicar(self.contexto()), aplicar=True)

    def _lanzar(self, o: ops.Operacion, orden: ops.Orden, aplicar: bool) -> bool:
        argv = list(orden.argv)
        if argv[0] in ("python3", "python"):
            argv[0] = rutas.interprete()
        programa = orden.cwd / argv[1] if len(argv) > 1 else None
        if programa is not None and not programa.is_file():
            self.aviso.emit(f"No existe {programa}.", "error")
            return False
        self._argv, self._id_en_curso, self._aplicando, self._lineas, self._inicio = argv, o.id, aplicar, [], time.monotonic()
        self._disciplina_en_curso = self._disciplina() if o.grupo != "laboratorio" else ""
        verbo = "Aplicando" if aplicar else ("Simulando" if o.escribe else "Ejecutando")
        nombre = f"{verbo}: {o.titulo}" + (f" · {self.modelos.id}" if o.sobre_modelo else (f" · {self._disciplina_en_curso}" if self._disciplina_en_curso else ""))
        entorno = {"MPLBACKEND": "Agg", "PYTHONDONTWRITEBYTECODE": "1"}
        self._worker = self.tareas.proceso(nombre, argv, cwd=str(orden.cwd), entorno=entorno,
                                           al_terminar=lambda codigo, i=o.id, a=aplicar, d=self._disciplina_en_curso: self._fin(codigo, i, a, d))
        self.cambiado.emit()
        self.corridaCambiada.emit()
        return True

    def _linea(self, texto: str, nivel: str) -> None:
        if self._worker is not None:
            self._lineas.append(texto)

    def _fin(self, codigo: int, id_: str, aplicar: bool, disciplina: str) -> None:
        self._worker = None
        segundos = time.monotonic() - self._inicio
        o = ops.operacion(id_)
        titulo = o.titulo if o else id_
        cuerpo = "\n".join(self._lineas[1:] if self._lineas and self._lineas[0].startswith("$ ") else self._lineas) + "\n"
        cabecera = (f"# {time.strftime('%Y-%m-%d %H:%M:%S')} · {'aplicado' if aplicar else 'simulación'} · {titulo}" + (f" · {disciplina}" if disciplina else "") + "\n"
                    f"# {' '.join(rutas.relativa(a) if str(a).startswith('/') else str(a) for a in self._argv)}\n# código de salida {codigo} · {segundos:.1f} s\n\n")
        self._escribir(id_, aplicar, cabecera + cuerpo)
        if codigo == 0:
            que = "aplicada" if aplicar else ("simulada" if o and o.escribe else "ejecutada")
            self.aviso.emit(f"{titulo} {que} en {segundos:.1f} s" + (": revisa la salida y aplica con Ctrl+Intro." if not aplicar and o and o.escribe else "."),
                            "positivo" if aplicar else "informacion")
        else:
            self.aviso.emit(f"{titulo} terminó con código {codigo} ({segundos:.1f} s): revisa la salida (F4).", "error")
        if id_ == "verificar_disciplina" and disciplina:
            archivos = {self.modelos._filas[r]["id"]: self.modelos.raiz / self.modelos._filas[r]["archivo"] for r in self.modelos._filas if r.startswith(disciplina + "/")}
            estados = self.modelos.estados.desde_salida_cli(disciplina, cuerpo, archivos)
            self.modelos.recargarEstados()
            self.consola.registrar("info", f"Estados actualizados: {len(estados)} modelos de {disciplina}")
        if id_ == "verificar_todo":
            for d in [x["nombre"] for x in self.modelos.disciplinas]:
                archivos = {self.modelos._filas[r]["id"]: self.modelos.raiz / self.modelos._filas[r]["archivo"] for r in self.modelos._filas if r.startswith(d + "/")}
                self.modelos.estados.desde_salida_cli(d, cuerpo, archivos)
            self.modelos.recargarEstados()
        if aplicar and id_ in ("catalogo", "web"):
            self.modelos.recargar()
        self.cambiado.emit()
        self.corridaCambiada.emit()
        self.terminada.emit(id_, aplicar, codigo)

    @Slot()
    def cancelar(self) -> None:
        if self.enCurso:
            self.tareas.cancelar()

    # ------------------------------------------------------------- plan y registro
    def _archivo(self, id_: str, aplicar: bool) -> Path:
        return self._cache / f"{id_}.{'registro' if aplicar else 'plan'}.txt"

    def _escribir(self, id_: str, aplicar: bool, texto: str) -> None:
        try:
            self._cache.mkdir(parents=True, exist_ok=True)
            self._archivo(id_, aplicar).write_text(texto, encoding="utf-8")
        except OSError as e:
            self.consola.registrar("warn", f"No se pudo guardar el {'registro' if aplicar else 'plan'}: {e}")

    def _leer(self, aplicar: bool) -> str:
        o = self._op()
        if o is None:
            return ""
        try:
            return self._archivo(o.id, aplicar).read_text(encoding="utf-8")
        except OSError:
            return ""

    @Property(str, notify=corridaCambiada)
    def plan(self) -> str:
        return self._leer(False)

    @Property(str, notify=corridaCambiada)
    def registro(self) -> str:
        return self._leer(True)

    def entradas_paleta(self, _texto: str) -> list[dict]:
        grupos = dict(ops.GRUPOS)
        return [{"nombre": f"op.ir.{o.id}", "texto": f"Operación: {o.titulo}", "grupo": grupos[o.grupo], "icono": o.icono,
                 "ejecutar": lambda i=o.id: self.fijar(i)} for o in ops.OPERACIONES]
