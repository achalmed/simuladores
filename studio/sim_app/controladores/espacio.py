"""studio/sim_app/controladores/espacio.py — lo transversal: la disciplina y el estado de verificación que filtran la
tabla (la navegación), el resumen y el contexto de la barra de estado, y las acciones sobre una ruta (abrir con el
sistema, Dolphin, terminal, portapapeles). Los filtros se recuerdan en QSettings."""
from __future__ import annotations

import os
import shutil
import subprocess

from gui_comun.qt import QGuiApplication, QObject, QSettings, Property, Signal, Slot

from sim_app.servicios import laboratorio as lab
from sim_app.servicios.verificaciones import ESTADOS, TEXTO_DE_ESTADO


class Espacio(QObject):
    filtroCambiado = Signal()
    resumenCambiado = Signal()
    contextoCambiado = Signal()
    aviso = Signal(str, str)

    def __init__(self, consola, ajustes=None, parent=None):
        super().__init__(parent)
        self.consola, self.ajustes = consola, ajustes
        self._s = QSettings()
        self._disciplina = str(self._s.value("ventana/disciplina", "") or "")
        self._estado = str(self._s.value("ventana/estado", "") or "")
        if self._estado not in TEXTO_DE_ESTADO:
            self._estado = ""
        self._disciplinas: list[str] = []
        self._resumen = self._contexto = ""

    def fijar_disciplinas(self, nombres: list[str]) -> None:
        self._disciplinas = list(nombres)
        if self._disciplina and self._disciplina not in self._disciplinas:
            self._disciplina = ""
            self.filtroCambiado.emit()

    # ------------------------------------------------------------- los filtros
    @Property(str, notify=filtroCambiado)
    def disciplina(self) -> str:
        return self._disciplina

    @Property(str, notify=filtroCambiado)
    def textoDisciplina(self) -> str:
        return lab.nombre_de(self._disciplina) if self._disciplina else "Todas las disciplinas"

    @Slot(str)
    def fijarDisciplina(self, nombre: str) -> None:
        nombre = nombre if nombre in self._disciplinas else ""
        if nombre != self._disciplina:
            self._disciplina = nombre
            self._s.setValue("ventana/disciplina", nombre)
            self.filtroCambiado.emit()

    @Property(str, notify=filtroCambiado)
    def estado(self) -> str:
        return self._estado

    @Property(str, notify=filtroCambiado)
    def textoEstado(self) -> str:
        return TEXTO_DE_ESTADO.get(self._estado, "Todos los estados")

    @Slot(str)
    def fijarEstado(self, estado: str) -> None:
        estado = estado if estado in TEXTO_DE_ESTADO else ""
        if estado != self._estado:
            self._estado = estado
            self._s.setValue("ventana/estado", estado)
            self.filtroCambiado.emit()

    @Property(str, notify=filtroCambiado)
    def nombreNavegacion(self) -> str:
        """La fila de la navegación que corresponde a los filtros (el estado manda si está puesto)."""
        if self._estado:
            return f"estado.{self._estado}"
        return f"disciplina.{self._disciplina}" if self._disciplina else "disciplina"

    @Property(str, notify=filtroCambiado)
    def textoFiltro(self) -> str:
        partes = []
        if self._disciplina:
            partes.append(lab.nombre_de(self._disciplina))
        if self._estado:
            partes.append(TEXTO_DE_ESTADO[self._estado].lower())
        return " · ".join(partes) or "todos los modelos"

    # ------------------------------------------------------------- barra de estado
    @Property(str, notify=resumenCambiado)
    def resumen(self) -> str:
        return self._resumen

    @Slot(str)
    def fijarResumen(self, texto: str) -> None:
        if texto != self._resumen:
            self._resumen = texto
            self.resumenCambiado.emit()

    @Property(str, notify=contextoCambiado)
    def contexto(self) -> str:
        return self._contexto

    @Slot(str)
    def fijarContexto(self, texto: str) -> None:
        if texto != self._contexto:
            self._contexto = texto
            self.contextoCambiado.emit()

    # ------------------------------------------------------------- sobre una ruta
    @Slot(str)
    def abrir(self, ruta: str) -> None:
        if ruta and os.path.exists(ruta):
            subprocess.Popen(["xdg-open", ruta])
            self.consola.registrar("info", f"Abierto con el sistema: {ruta}")
        else:
            self.aviso.emit(f"No existe: {ruta or '(nada seleccionado)'}", "aviso")

    @Slot(str)
    def abrirEnlace(self, url: str) -> None:
        if url:
            subprocess.Popen(["xdg-open", url])

    @Slot(str)
    def abrirDolphin(self, ruta: str) -> None:
        carpeta = ruta if os.path.isdir(ruta) else os.path.dirname(ruta)
        if os.path.isdir(carpeta):
            subprocess.Popen(["xdg-open", carpeta])
        else:
            self.aviso.emit(f"No existe la carpeta: {carpeta}", "aviso")

    def _terminal(self) -> str:
        preferido = (self.ajustes.terminal if self.ajustes is not None else "konsole") or "konsole"
        for candidato in (preferido, "konsole", "x-terminal-emulator"):
            if shutil.which(candidato):
                return candidato
        return ""

    @Slot(str)
    def abrirTerminal(self, ruta: str) -> None:
        carpeta = ruta if os.path.isdir(ruta) else os.path.dirname(ruta)
        if not os.path.isdir(carpeta):
            return
        terminal = self._terminal()
        if terminal == "konsole":
            subprocess.Popen(["konsole", "--workdir", carpeta])
        elif terminal:
            subprocess.Popen([terminal], cwd=carpeta)
        else:
            self.aviso.emit("No se encontró un emulador de terminal (konsole).", "aviso")

    @Slot(str)
    def copiar(self, texto: str) -> None:
        if texto:
            QGuiApplication.clipboard().setText(texto)
            self.consola.registrar("info", f"Copiado: {texto}")

    def entradas_paleta(self, _texto: str) -> list[dict]:
        salida = [{"nombre": "ir.disciplina", "texto": "Ver todas las disciplinas", "grupo": "Vistas", "icono": "view-list-tree",
                   "ejecutar": lambda: (self.fijarDisciplina(""), self.fijarEstado(""))}]
        salida += [{"nombre": f"ir.disciplina.{d}", "texto": f"Ver {lab.nombre_de(d)}", "grupo": "Vistas", "icono": lab.icono_de(d),
                    "ejecutar": lambda d=d: (self.fijarEstado(""), self.fijarDisciplina(d))} for d in self._disciplinas]
        salida += [{"nombre": f"ir.estado.{e}", "texto": f"Ver los modelos: {t.lower()}", "grupo": "Vistas", "icono": "checkmark",
                    "ejecutar": lambda e=e: self.fijarEstado(e)} for e, t in ESTADOS]
        return salida
