"""studio/sim_app/controladores/ajustes.py — «Configurar Simuladores Studio…»: la terminal, el intérprete de las CLI
y el entorno del studio (el .venv del repo), sobre QSettings."""
from __future__ import annotations

from gui_comun.qt import QObject, QSettings, Property, Signal, Slot

from sim_app.servicios import rutas


class Ajustes(QObject):
    cambiado = Signal()
    guardado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._s = QSettings()

    def _get(self, clave: str, defecto: str = "") -> str:
        return str(self._s.value(clave, defecto) or defecto)

    def _set(self, clave: str, v) -> None:
        if str(v) != self._get(clave):
            self._s.setValue(clave, v)
            self.cambiado.emit()

    terminal = Property(str, lambda self: self._get("sistema/terminal", "konsole"), lambda self, v: self._set("sistema/terminal", (v or "").strip() or "konsole"), notify=cambiado)
    figuraAcademica = Property(bool, lambda self: self._get("ventana/figura_academica", "false") == "true",
                               lambda self, v: self._set("ventana/figura_academica", "true" if v else "false"), notify=cambiado)

    @Property(str, constant=True)
    def interprete(self) -> str:
        return rutas.interprete()

    @Property(bool, constant=True)
    def hayVenv(self) -> bool:
        return rutas.hay_venv()

    @Property(str, constant=True)
    def ordenVenv(self) -> str:
        return rutas.orden_crear_venv()

    @Property(str, constant=True)
    def raiz(self) -> str:
        return str(rutas.raiz())

    @Slot()
    def guardar(self) -> None:
        self.cambiado.emit()
        self.guardado.emit()
