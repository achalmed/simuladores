"""La página de un modelo: su ficha, sus ecuaciones, sus escenarios y verificaciones, y el gráfico en vivo.

Todo sale del `Modelo` (contrato de `base.py`): los deslizadores son sus `parametros`, el gráfico es
`graficos._dibujar` (el mismo de la app y de los reportes) sobre una figura incrustada, los resultados son
`resultados(params)` y las verificaciones, sus teoremas e identidades. Ninguna página está escrita para un modelo.
"""
from __future__ import annotations

import html
import io
import subprocess
import sys

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QFormLayout, QSizePolicy, QFrame, QGridLayout, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QPushButton, QScrollArea, QSlider, QSplitter, QTabWidget,
                               QTextBrowser, QVBoxLayout, QWidget)

from gui_comun import diseno
from gui_comun.diseno import clase, icono_trazo, variante
from gui_comun.widgets.tarjetas import Tarjeta

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from sim_app.laboratorio import RAIZ


ANCHO_FORMULA = 440      # píxeles lógicos: lo más ancho que se dibuja una ecuación en la columna de la ficha

# Lo que LaTeX acepta y mathtext no: se traduce a lo equivalente que sí dibuja
_A_MATHTEXT = ((r"\tfrac", r"\frac"), (r"\dfrac", r"\frac"), (r"\text{", r"\mathrm{"), (r"\operatorname{", r"\mathrm{"),
               (r"\left", ""), (r"\right", ""), (r"\displaystyle", ""), (r"\big", ""), (r"\Big", ""),
               (r"\le ", r"\leq "), (r"\ge ", r"\geq "), (r"\lvert", "|"), (r"\rvert", "|"))


def formula(latex: str, color: str, tam: float = 13) -> QPixmap | None:
    """Una ecuación LaTeX dibujada con mathtext (la tipografía de las figuras); None si mathtext no la entiende."""
    from matplotlib import mathtext
    from matplotlib.font_manager import FontProperties
    import re
    # \text{con media} → \mathrm{con\ media}: en mathtext los espacios de \mathrm no cuentan
    latex = re.sub(r"\\text\{([^{}]*)\}", lambda m: r"\mathrm{" + m.group(1).replace(" ", r"\ ") + "}", latex)
    latex = re.sub(r"\\sqrt\s*([A-Za-z0-9])", r"\\sqrt{\1}", latex)   # \sqrt n → \sqrt{n}
    for de, a in _A_MATHTEXT:
        latex = latex.replace(de, a)
    buf = io.BytesIO()
    try:
        mathtext.math_to_image(f"${latex}$", buf, prop=FontProperties(size=tam, math_fontfamily="stix"), dpi=150,
                               format="png", color=color)
    except Exception:  # noqa: BLE001  una ecuación que mathtext no entiende se muestra como texto
        return None
    pix = QPixmap()
    pix.loadFromData(buf.getvalue(), "PNG")
    if pix.width() > ANCHO_FORMULA * 1.5:              # una ecuación larga se achica a la columna, no la ensancha
        pix = pix.scaledToWidth(int(ANCHO_FORMULA * 1.5), Qt.SmoothTransformation)
    pix.setDevicePixelRatio(1.5)
    return pix


class Deslizador(QWidget):
    """Un parámetro del modelo: nombre, valor con su unidad y un deslizador entre su mínimo y su máximo."""

    cambiado = Signal()

    def __init__(self, p):
        super().__init__()
        self.p = p
        self.pasos = max(1, round((p.maximo - p.minimo) / (p.paso or 0.1)))
        caja = QVBoxLayout(self)
        caja.setContentsMargins(0, 2, 0, 2)
        caja.setSpacing(2)
        fila = QHBoxLayout()
        nombre = QLabel(p.etiqueta or p.nombre)
        nombre.setWordWrap(True)
        if p.definicion:
            nombre.setToolTip(p.definicion)
        self.valor = clase(QLabel(), "suave")
        fila.addWidget(nombre, 1)
        fila.addWidget(self.valor)
        caja.addLayout(fila)
        self.barra = QSlider(Qt.Horizontal)
        self.barra.setRange(0, self.pasos)
        self.barra.valueChanged.connect(self._mover)
        caja.addWidget(self.barra)
        self.poner(p.valor)

    def actual(self) -> float:
        v = self.p.minimo + self.barra.value() * (self.p.maximo - self.p.minimo) / self.pasos
        return round(v, 10)

    def poner(self, v: float) -> None:
        self.barra.blockSignals(True)
        self.barra.setValue(round((v - self.p.minimo) / (self.p.maximo - self.p.minimo or 1) * self.pasos))
        self.barra.blockSignals(False)
        self._etiqueta()

    def _etiqueta(self) -> None:
        v = self.actual()
        texto = f"{v:,.0f}" if float(v).is_integer() and abs(v) >= 10 else f"{v:,.3g}"
        self.valor.setText(texto.replace(",", " ") + (f" {self.p.unidad}" if self.p.unidad else ""))

    def _mover(self) -> None:
        self._etiqueta()
        self.cambiado.emit()


class PaginaModelo(QWidget):
    volver = Signal()

    def __init__(self, ventana, disciplina: str, fila_catalogo: dict):
        super().__init__()
        self.ventana, self.disciplina, self.cat = ventana, disciplina, fila_catalogo
        self.lab = ventana.lab
        self.m = self.lab.modelo(disciplina, fila_catalogo["id"])
        self.dibujar_pronto = QTimer(self, singleShot=True, interval=50, timeout=self._dibujar)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 16, 24, 16)
        raiz.setSpacing(12)
        cabeza = QHBoxLayout()
        atras = variante(QPushButton(icono_trazo("volver"), " Volver"), "fantasma")
        atras.clicked.connect(self.volver.emit)
        cabeza.addWidget(atras, 0, Qt.AlignTop)
        insignia = QLabel(self.m.id or fila_catalogo["id"])
        insignia.setObjectName("mosaicoIcono")
        insignia.setAlignment(Qt.AlignCenter)
        insignia.setFixedSize(52, 40)
        insignia.setStyleSheet("font-weight: 700;")
        cabeza.addWidget(insignia, 0, Qt.AlignTop)
        textos = QVBoxLayout()
        textos.setSpacing(2)
        titulo = QLabel(fila_catalogo["titulo"])
        titulo.setObjectName("tituloPagina")
        sub = QLabel((self.m.ficha.pregunta if self.m.ficha and self.m.ficha.pregunta else fila_catalogo["seccion"]))
        sub.setObjectName("subtituloPagina")
        sub.setWordWrap(True)
        textos.addWidget(titulo)
        textos.addWidget(sub)
        cabeza.addLayout(textos, 1)
        recorrido = QPushButton(icono_trazo("jugar"), " Recorrido guiado")
        recorrido.setToolTip("La app pedagógica paso a paso (pregunta → ecuaciones → curvas → experimentos)")
        recorrido.clicked.connect(self._recorrido)
        cabeza.addWidget(recorrido, 0, Qt.AlignTop)
        raiz.addLayout(cabeza)

        divisor = QSplitter(Qt.Horizontal)
        divisor.setChildrenCollapsible(False)
        divisor.addWidget(self._pestanas())
        divisor.addWidget(self._lado_grafico())
        divisor.setStretchFactor(0, 2)
        divisor.setStretchFactor(1, 3)
        divisor.setSizes([520, 780])
        raiz.addWidget(divisor, 1)
        QTimer.singleShot(0, self._dibujar)

    # ------------------------------------------------------------------------------------------- columna izquierda
    def _pestanas(self) -> QWidget:
        tabs = QTabWidget()
        t = diseno._ACTUAL or diseno.tokens("oscuro", "lima")
        F = self.m.ficha
        texto = QTextBrowser()
        texto.setOpenExternalLinks(True)
        texto.setFrameShape(QFrame.NoFrame)
        texto.setHtml(self._html_ficha(F, t) if F else "<p>Este modelo no trae ficha.</p>")
        tabs.addTab(texto, "Ficha")

        ecu = QWidget()
        lista = QVBoxLayout(ecu)
        lista.setSpacing(14)
        for e in (F.ecuaciones if F else []):
            caja = Tarjeta(e.nombre)
            pix = formula(e.latex, t["texto"])
            if pix is not None:
                img = QLabel()
                img.setPixmap(pix)
                caja.cuerpo.addWidget(img)
            else:
                crudo = clase(QLabel(e.latex), "suave")
                crudo.setWordWrap(True)
                crudo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
                caja.cuerpo.addWidget(crudo)
            sig = clase(QLabel(e.significado), "suave")
            sig.setWordWrap(True)
            sig.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            caja.cuerpo.addWidget(sig)
            lista.addWidget(caja)
        if F and F.derivacion:
            der = Tarjeta("Derivación")
            for paso in F.derivacion:
                pix = formula(paso, t["texto"], 12)
                w = QLabel()
                if pix is not None:
                    w.setPixmap(pix)
                else:
                    w.setText(paso)
                    w.setWordWrap(True)
                    w.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
                der.cuerpo.addWidget(w)
            lista.addWidget(der)
        lista.addStretch(1)
        tabs.addTab(_desplazable(ecu), "Ecuaciones")

        esc = QWidget()
        lista_esc = QVBoxLayout(esc)
        lista_esc.setSpacing(10)
        self.lectura = QTextBrowser()
        self.lectura.setFrameShape(QFrame.NoFrame)
        self.lectura.setMinimumHeight(150)
        for e in self.m.escenarios:
            b = QPushButton(e.descripcion)
            b.setToolTip(f"Aplica: {', '.join(f'{k} = {v}' for k, v in e.cambios.items())}")
            b.setStyleSheet("text-align: left;")
            b.clicked.connect(lambda _=False, e=e: self._escenario(e))
            lista_esc.addWidget(b)
        if not self.m.escenarios:
            lista_esc.addWidget(clase(QLabel("Este modelo no trae escenarios."), "vacio"))
        lista_esc.addWidget(self.lectura, 1)
        tabs.addTab(_desplazable(esc), "Escenarios")

        ver = QWidget()
        caja_ver = QVBoxLayout(ver)
        self.lista_ver = QListWidget()
        self.lista_ver.setWordWrap(True)
        b_ver = variante(QPushButton("Comprobar las verificaciones"), "primario")
        b_ver.clicked.connect(self._verificar)
        caja_ver.addWidget(clase(QLabel("Identidades, convergencias y teoremas que el modelo debe cumplir."), "suave"))
        caja_ver.addWidget(b_ver, 0, Qt.AlignLeft)
        caja_ver.addWidget(self.lista_ver, 1)
        tabs.addTab(ver, "Verificaciones")
        return tabs

    def _html_ficha(self, F, t) -> str:
        e = html.escape

        def seccion(titulo: str, cuerpo: str) -> str:
            return (f"<h3 style='color:{t['texto_suave']}; font-size:12px; text-transform:uppercase; "
                    f"margin:14px 0 4px'>{titulo}</h3>{cuerpo}") if cuerpo else ""

        def lista(items) -> str:
            return "<ul>" + "".join(f"<li>{e(str(i))}</li>" for i in items) + "</ul>" if items else ""

        variables = "".join(f"<li><b>{e(str(s))}</b>: {e(str(d))}</li>" for s, d in (F.variables or []))
        partes = [seccion("Contexto", f"<p>{e(F.contexto)}</p>"), seccion("Autores", f"<p>{e(F.autores)}</p>"),
                  seccion("Supuestos", lista(F.supuestos)), seccion("Variables", f"<ul>{variables}</ul>" if variables else ""),
                  seccion("Intuición", f"<p>{e(F.intuicion)}</p>"),
                  seccion("Equilibrio", f"<p>{e(F.equilibrio)}</p>" if F.equilibrio else ""),
                  seccion("Limitaciones", lista(F.limitaciones)),
                  seccion("Lo que viene después", f"<p>{e(F.evolucion)}</p>" if F.evolucion else ""),
                  seccion("Procedencia", f"<p>{e(F.procedencia)}</p>" if F.procedencia else "")]
        return f"<div style='line-height:1.45; color:{t['texto']}'>{''.join(partes)}</div>"

    # -------------------------------------------------------------------------------------------- columna derecha
    def _lado_grafico(self) -> QWidget:
        lado = QWidget()
        caja = QVBoxLayout(lado)
        caja.setContentsMargins(8, 0, 0, 0)
        caja.setSpacing(12)
        papel = Tarjeta()
        self.figura = Figure(figsize=(7, 4.4), dpi=100, facecolor="white")
        self.ejes = self.figura.add_subplot(111)
        self.lienzo = FigureCanvasQTAgg(self.figura)
        self.lienzo.setMinimumHeight(320)
        papel.cuerpo.addWidget(self.lienzo, 1)
        papel.setStyleSheet("QFrame[clase='tarjeta'] { background: #ffffff; }")
        caja.addWidget(papel, 3)

        fila = QHBoxLayout()
        fila.setSpacing(12)
        params = Tarjeta("Parámetros", self._boton_restablecer())
        rejilla = QWidget()
        forma = QGridLayout(rejilla)
        forma.setContentsMargins(0, 0, 0, 0)
        forma.setHorizontalSpacing(18)
        self.deslizadores = {}
        for i, p in enumerate(self.m.parametros):
            d = Deslizador(p)
            d.cambiado.connect(self.dibujar_pronto.start)
            self.deslizadores[p.nombre] = d
            forma.addWidget(d, i // 2, i % 2)
        params.cuerpo.addWidget(_desplazable(rejilla))
        fila.addWidget(params, 3)
        res = Tarjeta("Resultados")
        self.resultados = QFormLayout()
        self.resultados.setVerticalSpacing(6)
        res.cuerpo.addLayout(self.resultados)
        res.cuerpo.addStretch(1)
        fila.addWidget(res, 2)
        caja.addLayout(fila, 2)
        return lado

    def _boton_restablecer(self) -> QPushButton:
        b = variante(QPushButton("Restablecer"), "fantasma")
        b.clicked.connect(self._restablecer)
        return b

    # ------------------------------------------------------------------------------------------------- acciones
    def params(self) -> dict:
        return {n: d.actual() for n, d in self.deslizadores.items()}

    def _dibujar(self) -> None:
        self.lab.activar(self.disciplina)
        try:
            self.lab.graficos()._dibujar(self.ejes, self.m, self.params())
            self.ejes.set_xlabel(self.m.xlabel)
            self.ejes.set_ylabel(self.m.ylabel)
            self.figura.tight_layout()
        except Exception as e:  # noqa: BLE001  un parámetro fuera de dominio no tumba la ventana
            self.ejes.clear()
            self.ejes.text(0.5, 0.5, f"No se pudo calcular:\n{e}", ha="center", va="center", transform=self.ejes.transAxes)
        self.lienzo.draw_idle()
        self._resultados()

    def _resultados(self) -> None:
        while self.resultados.rowCount():
            self.resultados.removeRow(0)
        if not self.m.resultados:
            self.resultados.addRow(clase(QLabel("Este modelo no declara resultados."), "tenue"))
            return
        try:
            datos = self.m.resultados(self.params())
        except Exception as e:  # noqa: BLE001
            self.resultados.addRow(clase(QLabel(f"No se pudo calcular: {e}"), "tenue"))
            return
        for nombre, valor in list(datos.items())[:12]:
            etiqueta = clase(QLabel(str(nombre)), "suave")
            etiqueta.setWordWrap(True)
            texto = f"{valor:,.4g}".replace(",", " ") if isinstance(valor, (int, float)) else str(valor)
            v = QLabel(texto)
            v.setStyleSheet("font-weight: 600;")
            v.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.resultados.addRow(etiqueta, v)

    def _restablecer(self) -> None:
        for p in self.m.parametros:
            self.deslizadores[p.nombre].poner(p.valor)
        self._dibujar()

    def _escenario(self, e) -> None:
        self._restablecer()
        for nombre, valor in e.cambios.items():
            if nombre in self.deslizadores:
                self.deslizadores[nombre].poner(valor)
        self._dibujar()
        t = diseno._ACTUAL or diseno.tokens("oscuro", "lima")
        cadena = "".join(f"<li>{html.escape(str(p))}</li>" for p in (e.cadena or []))
        cambios = ", ".join(f"{html.escape(str(k))} = {v}" for k, v in e.cambios.items())
        self.lectura.setHtml(f"<div style='color:{t['texto']}; line-height:1.45'><p><b>{html.escape(e.descripcion)}</b>"
                             f"<br><span style='color:{t['texto_suave']}'>{cambios}</span></p>"
                             + (f"<p>{html.escape(e.lectura)}</p>" if e.lectura else "")
                             + (f"<p><b>Mecanismo</b></p><ol>{cadena}</ol>" if cadena else "") + "</div>")

    def _verificar(self) -> None:
        self.lab.activar(self.disciplina)
        self.lista_ver.clear()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        bien = 0
        try:
            for v in self.m.verificaciones:
                try:
                    ok, detalle = v.fn()
                except Exception as e:  # noqa: BLE001
                    ok, detalle = False, f"{type(e).__name__}: {e}"
                bien += bool(ok)
                item = QListWidgetItem(icono_trazo("jugar" if ok else "quitar"), f"{v.nombre}\n{detalle}")
                self.lista_ver.addItem(item)
        finally:
            QApplication.restoreOverrideCursor()
        n = len(self.m.verificaciones)
        self.ventana.marco.avisar(f"{bien} de {n} verificaciones", self.cat["titulo"], "ok" if bien == n else "error")

    def _recorrido(self) -> None:
        subprocess.Popen([sys.executable, "main.py"], cwd=str(RAIZ / self.disciplina))
        self.ventana.marco.avisar("Recorrido guiado", "Se abre en su propia ventana: elige el modelo en su menú.", "info")


def _desplazable(w: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    area.setWidget(w)
    return area
