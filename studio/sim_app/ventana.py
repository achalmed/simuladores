"""La ventana de Simuladores Studio: el marco común de los studios (gui_comun) sobre el laboratorio.

Barra lateral: Inicio y una página por disciplina (Macroeconomía, Estadística…), con sus modelos por sección leídos de
`catalogo.json`. Abrir un modelo lo importa (con su disciplina activa) y muestra su página: ficha, ecuaciones,
escenarios, verificaciones y el gráfico en vivo con sus parámetros. La paleta (Ctrl+K) encuentra cualquier modelo.
"""
from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMainWindow, QMessageBox, QStackedWidget, QVBoxLayout, QWidget)

from gui_comun.diseno import clase, icono_trazo
from gui_comun.theming import aplicar_tema, disenador_de
from gui_comun.widgets.console_dock import ConsoleDock
from gui_comun.widgets.marco import montar_studio
from gui_comun.widgets.paleta import Comando
from gui_comun.widgets.tarjetas import (Cifra, Mosaico, encabezado, pagina_desplazable, rejilla_pareja, seccion)

from sim_app.laboratorio import NOMBRES, Laboratorio, catalogo

APP_VERSION = "1.0.0"
ACENTO = "lima"
LOGO = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#888888" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M6 15c3-6 6-9 13-10"/>'
        '<circle cx="12" cy="9" r="1.5"/></svg>')
ICONO_DISCIPLINA = {"macro": "tendencia", "estadistica": "barras"}


class Ajustes:
    def __init__(self) -> None:
        self.q = QSettings()

    def theme(self) -> str:
        return str(self.q.value("ui/tema", "sistema"))

    def set_theme(self, tema: str) -> None:
        self.q.setValue("ui/tema", tema)


class PaginaDisciplina(QWidget):
    """Los modelos de una disciplina por sección, con un buscador."""

    def __init__(self, ventana, disciplina: str, filas: list[dict]):
        super().__init__()
        self.ventana, self.disciplina = ventana, disciplina
        self.filas = sorted(filas, key=lambda f: (f["nivel"], f["id"]))
        contenido = QWidget()
        self.raiz = QVBoxLayout(contenido)
        self.raiz.setSpacing(12)
        cabeza = QHBoxLayout()
        verif = sum(f["verificaciones"] for f in filas)
        cabeza.addWidget(encabezado(NOMBRES.get(disciplina, disciplina.capitalize()),
                                    f"{len(filas)} modelos · {verif} verificaciones · cada uno con su ficha, sus "
                                    "escenarios y su gráfico en vivo"), 1)
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Filtrar modelos…")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.setFixedWidth(240)
        clase(self.buscador, "busqueda")
        self.buscador.textChanged.connect(self._pintar)
        cabeza.addWidget(self.buscador, 0, Qt.AlignTop)
        self.raiz.addLayout(cabeza)
        self.cuerpo = QVBoxLayout()
        self.cuerpo.setSpacing(10)
        self.raiz.addLayout(self.cuerpo)
        self.raiz.addStretch(1)
        fuera = QVBoxLayout(self)
        fuera.setContentsMargins(0, 0, 0, 0)
        fuera.addWidget(pagina_desplazable(contenido))
        self._pintar("")

    def _pintar(self, texto: str) -> None:
        while self.cuerpo.count():
            item = self.cuerpo.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                _vaciar(item.layout())
        texto = texto.strip().lower()
        visibles = [f for f in self.filas if not texto or texto in
                    f"{f['id']} {f['titulo']} {f['seccion']} {f['ficha'].get('pregunta', '')}".lower()]
        secciones: dict[str, list[dict]] = {}
        for f in visibles:
            secciones.setdefault(f["seccion"], []).append(f)
        for nombre, filas in secciones.items():
            self.cuerpo.addSpacing(4)
            self.cuerpo.addWidget(seccion(f"{nombre} · {len(filas)}"))
            rejilla = rejilla_pareja(3)
            for i, f in enumerate(filas):
                pregunta = f["ficha"].get("pregunta") or f["seccion"]
                rejilla.addWidget(Mosaico(icono_trazo(ICONO_DISCIPLINA.get(self.disciplina, "tendencia")),
                                          f"{f['id']} · {f['titulo']}", pregunta,
                                          lambda f=f: self.ventana.abrir_modelo(self.disciplina, f)), i // 3, i % 3)
            self.cuerpo.addLayout(rejilla)
        if not visibles:
            self.cuerpo.addWidget(clase(QLabel("Ningún modelo coincide."), "vacio"))


def _vaciar(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            _vaciar(item.layout())


class Ventana:
    """Envoltorio de la QMainWindow con la forma que `gui_comun.widgets.marco.montar_studio` espera."""

    def __init__(self) -> None:
        app = QApplication.instance()
        self.settings = Ajustes()
        disenador = disenador_de(app) or aplicar_tema(app, self.settings.theme(), acento=ACENTO)
        self.lab = Laboratorio()
        self.cat = catalogo()
        self.ui = QMainWindow()
        self.ui.setWindowTitle(f"Simuladores Studio {APP_VERSION}")
        central = QWidget()
        fila = QHBoxLayout(central)
        self.ui.sidebar = QListWidget()
        self.ui.stack = QStackedWidget()
        fila.addWidget(self.ui.sidebar)
        fila.addWidget(self.ui.stack, 1)
        self.ui.setCentralWidget(central)
        self.ui.statusbar = self.ui.statusBar()
        self.console = ConsoleDock(self.ui)
        self.ui.addDockWidget(Qt.BottomDockWidgetArea, self.console)
        self._workers: list = []
        self._modelos: dict[str, QWidget] = {}

        self.controllers: dict[str, SimpleNamespace] = {}
        self._page_order: list[str] = []
        self._pagina("dashboard", "Inicio", "inicio", self._crear_inicio())
        for d in self.cat["disciplinas"]:
            filas = [f for f in self.cat["modelos"] if f["disciplina"] == d]
            self._pagina(d, NOMBRES.get(d, d.capitalize()), ICONO_DISCIPLINA.get(d, "tendencia"),
                         PaginaDisciplina(self, d, filas))
        self.ui.sidebar.currentRowChanged.connect(lambda fila: self.ui.stack.setCurrentIndex(fila))
        self.ui.sidebar.setCurrentRow(0)

        self.marco = montar_studio(self, nombre="Simuladores Studio", subtitulo="Laboratorio computacional",
                                   logo_svg=LOGO, disenador=disenador, primarios={}, peligro=())
        for f in self.cat["modelos"]:
            self.marco.comandos_extra.append(
                Comando(f"{f['id']} · {f['titulo']}", lambda f=f: self.abrir_modelo(f["disciplina"], f),
                        grupo=NOMBRES.get(f["disciplina"], f["disciplina"]),
                        icono=icono_trazo(ICONO_DISCIPLINA.get(f["disciplina"], "tendencia")),
                        palabras=f"{f['seccion']} {f['ficha'].get('pregunta', '')}"))

    def _crear_inicio(self) -> QWidget:
        contenido = QWidget()
        raiz = QVBoxLayout(contenido)
        raiz.setSpacing(14)
        raiz.addWidget(encabezado("Inicio", "Cada teoría o método como modelo ejecutable: se deriva, se simula y se "
                                            "ve. Mueve sus parámetros y mira cómo cambia el equilibrio."))
        modelos = self.cat["modelos"]
        cifras = rejilla_pareja(4)
        for i, c in enumerate((Cifra("Modelos", str(len(modelos)), "con ficha pedagógica completa"),
                               Cifra("Disciplinas", str(len(self.cat["disciplinas"])), "un motor común"),
                               Cifra("Verificaciones", f"{sum(f['verificaciones'] for f in modelos):,}".replace(",", " "),
                                     "identidades y teoremas"),
                               Cifra("Escenarios", str(sum(len(f["escenarios"]) for f in modelos)),
                                     "experimentos con su lectura"))):
            cifras.addWidget(c, 0, i)
        raiz.addLayout(cifras)
        raiz.addSpacing(4)
        raiz.addWidget(seccion("Disciplinas"))
        rejilla = rejilla_pareja(2)
        for i, d in enumerate(self.cat["disciplinas"]):
            filas = [f for f in modelos if f["disciplina"] == d]
            secciones = list(dict.fromkeys(f["seccion"] for f in sorted(filas, key=lambda f: f["nivel"])))
            rejilla.addWidget(Mosaico(icono_trazo(ICONO_DISCIPLINA.get(d, "tendencia")),
                                      f"{NOMBRES.get(d, d.capitalize())} · {len(filas)} modelos",
                                      " · ".join(secciones[:4]) + (" …" if len(secciones) > 4 else ""),
                                      lambda d=d: self.navigate(d)), i // 2, i % 2)
        raiz.addLayout(rejilla)
        raiz.addStretch(1)
        return pagina_desplazable(contenido)

    # ----------------------------------------------------------------------------------------------------- API
    def show(self) -> None:
        self.ui.show()

    def navigate(self, page_id: str) -> None:
        if page_id in self._page_order:
            self.ui.sidebar.setCurrentRow(self._page_order.index(page_id))

    def abrir_modelo(self, disciplina: str, fila: dict) -> None:
        clave = f"{disciplina}/{fila['id']}"
        pagina = self._modelos.get(clave)
        if pagina is None:
            from sim_app.pagina_modelo import PaginaModelo
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                pagina = PaginaModelo(self, disciplina, fila)
            except Exception as e:  # noqa: BLE001  un modelo roto no tumba la ventana
                self.marco.avisar(f"No se pudo abrir {fila['id']}", str(e), "error")
                return
            finally:
                QApplication.restoreOverrideCursor()
            pagina.volver.connect(lambda: self.ui.stack.setCurrentIndex(max(0, self.ui.sidebar.currentRow())))
            self.ui.stack.addWidget(pagina)
            self._modelos[clave] = pagina
        if disciplina in self._page_order:
            self.ui.sidebar.blockSignals(True)
            self.ui.sidebar.setCurrentRow(self._page_order.index(disciplina))
            self.ui.sidebar.blockSignals(False)
        self.ui.stack.setCurrentWidget(pagina)

    def run_function_worker(self, worker, nombre: str) -> None:   # lo pide el marco
        self.console.attach_function_worker(worker, nombre)
        self._workers.append(worker)
        worker.start()

    # ------------------------------------------------------------------------------------------------- privado
    def _pagina(self, id_: str, nombre: str, icono: str, widget) -> None:
        self.controllers[id_] = SimpleNamespace(widget=widget)
        self._page_order.append(id_)
        self.ui.stack.addWidget(widget)
        self.ui.sidebar.addItem(QListWidgetItem(icono_trazo(icono), nombre))

    def _open_preferences(self) -> None:
        self.navigate("dashboard")

    def _about(self) -> None:
        QMessageBox.about(self.ui, "Acerca de Simuladores Studio",
                          f"<b>Simuladores Studio</b> {APP_VERSION}<br><br>El laboratorio computacional: cada teoría "
                          "o método como modelo ejecutable con su ficha pedagógica, sus escenarios y sus "
                          "verificaciones.<br><br>Los mismos modelos alimentan los reportes, la app de recorrido "
                          "guiado y los cursos de los pubs.<br><br>Edison Achalma")
