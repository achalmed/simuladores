"""studio/sim_app/controladores/modelos.py — el catálogo de modelos (de `catalogo.json`, sin importar nada) con su estado
de verificación y su última corrida (la lista del catálogo); el modelo actual, importado al elegirlo con su disciplina
activa (`servicios.laboratorio`): su ficha en Markdown, sus parámetros (los deslizadores), sus escenarios (los del
modelo y los propios del studio), la corrida (lo que dibuja `GraficoCientifico`, magnitudes frente a la base) y sus
verificaciones (`ListaDiagnosticos`). Correr y verificar calculan en proceso con el motor y escriben solo la caché
del studio; guardar un escenario escribe en los datos del studio; exportar los datos escribe en salidas/ de la
disciplina, siempre tras confirmar (`controladores.operaciones`).

Reingeniería (2026-11-02, `docs/reingenieria.md`): el espacio de simulación. Al abrir un modelo se calculan la base y el
escenario (y se verifica si no tiene estado); mover un parámetro recalcula en vivo (L4); los gráficos de la base y del
escenario van con su x real y los roles de color del tema (`servicios.simulacion`, L2–L3); la sensibilidad de un
parámetro se barre con `base.sensibilidad` (L6); y `validez` dice si la corrida puede presentarse como válida (L8)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from gui_comun.modelos import ModeloFiltrado, ModeloLista, ModeloTabla
from gui_comun.qt import QObject, QStandardPaths, QTimer, Property, Signal, Slot

from sim_app.servicios import corridas, fichas, formulas, rutas
from sim_app.servicios import simulacion as sim
from sim_app.servicios import laboratorio as lab
from sim_app.servicios import verificaciones as ver

COLUMNAS = [("Id", "id"), ("Modelo", "titulo"), ("Sección", "seccion"), ("Parámetros", "parametros"), ("Escenarios", "escenarios"),
            ("Verificaciones", "verificaciones"), ("Estado", "estado"), ("Última corrida", "corrida")]
COLUMNAS_RESULTADOS = [("Magnitud", "magnitud"), ("Base", "base"), ("Escenario", "escenario"), ("Δ", "delta"), ("Δ %", "pct")]
ROLES_VERIFICACIONES = ("nivel", "mensaje", "archivo", "linea", "detalle", "fuente", "ok")
ORDEN_ESTADO = {"diferencias": 0, "sin_verificar": 1, "verificado": 2}
ROLES_CATALOGO = ("ref", "id", "titulo", "disciplina", "textoDisciplina", "seccion", "nivelCurricular", "pregunta", "clave", "estado", "nivel",
                  "parametros", "escenarios", "verificaciones", "icono")
ESPERA_VIVO_MS = 150
TOPE_VIVO_MS = 400


def cache_del_studio() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation) or (Path.home() / ".cache" / "simuladores-studio"))


def datos_del_studio() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) or (Path.home() / ".local" / "share" / "simuladores-studio"))


class Modelos(QObject):
    cambiado = Signal()                 # la tabla, los estados, los contadores
    actualCambiado = Signal()           # el modelo actual (ficha, parámetros, escenarios)
    valoresCambiados = Signal()         # los valores del escenario en edición
    corridaCambiada = Signal()          # la última corrida (gráfico, resultados, registro)
    verificacionCambiada = Signal()     # las verificaciones del modelo actual
    figuraCambiada = Signal()
    sensibilidadCambiada = Signal()
    vivoCambiado = Signal()
    seleccionar = Signal(int)           # QML: selecciona esa fila visible de la tabla
    aviso = Signal(str, str)

    def __init__(self, espacio, consola, cache: Path | None = None, datos: Path | None = None, raiz: Path | None = None, parent=None):
        super().__init__(parent)
        self.espacio, self.consola = espacio, consola
        self.raiz = raiz or rutas.raiz()
        self._cache = cache or cache_del_studio()
        self._datos = datos or datos_del_studio()
        self.lab = lab.Laboratorio(self.raiz)
        self.estados = ver.Estados(self._cache / "verificaciones.json")
        self._tabla = ModeloTabla(COLUMNAS, parent=self)
        self._modelo = ModeloFiltrado(self._tabla, parent=self)
        self._resultados = ModeloTabla(COLUMNAS_RESULTADOS, parent=self)
        self._verificaciones = ModeloLista(ROLES_VERIFICACIONES, parent=self)
        self._catalogo: dict = {}
        self._filas: dict[str, dict] = {}            # ref → fila del catálogo
        self._orden: list[str] = []
        self._actual = ""
        self._m = None                                # el Modelo importado
        self._archivo: Path | None = None
        self._motivo = ""
        self._ficha = ""
        self._color_texto = "#000000"
        self._valores: dict = {}
        self._escenario = "base"
        self._propios: dict = {}
        self._corrida: dict = {}
        self._grafico: dict = {}
        self._registro = ""
        self._figura = ""
        self._base: dict = {}                         # la corrida de la base (valores por defecto)
        self._grafico_base: dict = {}
        self._sens: dict = {}
        self._sens_param = ""
        self._sens_magnitud = ""
        self._vivo = True                             # el usuario lo quiere
        self._vivo_modelo = True                      # el modelo es bastante rápido (L4)
        self._ms = 0.0
        self.verificar_al_abrir = True
        self._lista = ModeloLista(ROLES_CATALOGO, parent=self)
        self._catalogo_filtrado = ModeloFiltrado(self._lista, parent=self)
        self._busqueda = ""
        self._catalogo_filtrado.aceptar_con(self._acepta_catalogo)
        self._espera = QTimer(self)
        self._espera.setSingleShot(True)
        self._espera.setInterval(ESPERA_VIVO_MS)
        self._espera.timeout.connect(lambda: self.correr(en_vivo=True))
        self._modelo.aceptar_con(self._acepta)
        espacio.filtroCambiado.connect(lambda: (self._modelo.aceptar_con(self._acepta), self._catalogo_filtrado.aceptar_con(self._acepta_catalogo)))
        self.recargar()

    modelo = Property(QObject, lambda self: self._modelo, constant=True)
    resultadosModelo = Property(QObject, lambda self: self._resultados, constant=True)
    verificacionesModelo = Property(QObject, lambda self: self._verificaciones, constant=True)
    catalogo = Property(QObject, lambda self: self._catalogo_filtrado, constant=True)

    # ------------------------------------------------------------------ el catálogo (la lista de la izquierda)
    def _acepta_catalogo(self, fila: int) -> bool:
        f = self._lista.fila(fila)
        if self.espacio.disciplina and f.get("disciplina") != self.espacio.disciplina:
            return False
        if self.espacio.estado and f.get("clave") != self.espacio.estado:
            return False
        if self._busqueda:
            texto = f"{f.get('id', '')} {f.get('titulo', '')} {f.get('seccion', '')} {f.get('pregunta', '')}".lower()
            return all(p in texto for p in self._busqueda.lower().split())
        return True

    @Slot(str)
    def buscar(self, texto: str) -> None:
        texto = (texto or "").strip()
        if texto != self._busqueda:
            self._busqueda = texto
            self._catalogo_filtrado.aceptar_con(self._acepta_catalogo)
            self.cambiado.emit()

    def _fila_catalogo(self, f: dict, tabla: dict) -> dict:
        return {"ref": f["ref"], "id": f["id"], "titulo": f["titulo"], "disciplina": f["disciplina"], "textoDisciplina": lab.nombre_de(f["disciplina"]),
                "seccion": f.get("seccion") or "", "nivelCurricular": f.get("nivel") or 0, "pregunta": (f.get("ficha") or {}).get("pregunta", ""),
                "clave": tabla["clave"], "estado": tabla["estado"], "nivel": tabla["nivel"], "parametros": len(f.get("parametros", [])),
                "escenarios": len(f.get("escenarios", [])), "verificaciones": f.get("verificaciones", 0), "icono": lab.icono_de(f["disciplina"])}

    def _pintar_catalogo(self) -> None:
        tabla = {t["ref"]: t for t in self._tabla.todas()}
        self._lista.poner([self._fila_catalogo(f, tabla[r]) for r, f in self._filas.items() if r in tabla])

    @Property(int, notify=cambiado)
    def visibles(self) -> int:
        return self._catalogo_filtrado.rowCount()

    # ------------------------------------------------------------------ la tabla
    def _acepta(self, fila_origen: int) -> bool:
        f = self._tabla.fila(fila_origen)
        if self.espacio.disciplina and f.get("disciplina") != self.espacio.disciplina:
            return False
        return not self.espacio.estado or f.get("clave") == self.espacio.estado

    def _archivo_de(self, f: dict) -> Path | None:
        return (self.raiz / f["archivo"]) if f.get("archivo") else None

    def _fila(self, f: dict) -> dict:
        ref = f["ref"]
        estado = self.estados.estado(ref, self._archivo_de(f))
        corrida = self._fecha_corrida(ref)
        pregunta = (f.get("ficha") or {}).get("pregunta", "")
        return {"id": f["id"], "titulo": f["titulo"], "seccion": f.get("seccion") or "—", "parametros": str(len(f.get("parametros", []))),
                "escenarios": str(len(f.get("escenarios", []))), "verificaciones": str(f.get("verificaciones", 0)),
                "estado": ver.TEXTO_DE_ESTADO[estado], "corrida": corrida or "—", "nivel": ver.NIVEL_DE_ESTADO[estado],
                "icono": {"titulo": lab.icono_de(f["disciplina"])}, "habilitado": True, "clave": estado, "ref": ref, "disciplina": f["disciplina"],
                "nivelCurricular": f.get("nivel") or 0, "pregunta": pregunta,
                "crudo": {"estado": ORDEN_ESTADO.get(estado, 9), "parametros": len(f.get("parametros", [])), "escenarios": len(f.get("escenarios", [])),
                          "verificaciones": f.get("verificaciones", 0), "seccion": f.get("nivel") or 99, "corrida": corrida}}

    @Slot()
    def recargar(self) -> None:
        """Relee el catálogo y los estados (F6, o al regenerar el catálogo)."""
        self._catalogo = lab.catalogo(self.raiz)
        self._filas = {f["ref"]: f for f in self._catalogo.get("modelos", [])}
        self._orden = list(self._filas)
        self.espacio.fijar_disciplinas(list(self._catalogo.get("disciplinas", [])))
        self._tabla.poner([self._fila(f) for f in self._filas.values()])
        self._pintar_catalogo()
        self.cambiado.emit()
        if self._actual and self._actual not in self._filas:
            self._fijar_actual("")

    def recargarEstados(self) -> None:
        """Vuelve a leer el estado de cada fila (tras `main.py verificar` de una disciplina)."""
        self.estados = ver.Estados(self._cache / "verificaciones.json")
        for i, f in enumerate(self._tabla.todas()):
            self._tabla.actualizar(i, **self._fila(self._filas[f["ref"]]))
        self._pintar_catalogo()
        self.cambiado.emit()
        self.verificacionCambiada.emit()

    def _actualizar_fila(self, ref: str) -> None:
        for i, f in enumerate(self._tabla.todas()):
            if f["ref"] == ref:
                fila = self._fila(self._filas[ref])
                self._tabla.actualizar(i, **fila)
                for j, g in enumerate(self._lista.todas()):
                    if g["ref"] == ref:
                        self._lista.actualizar(j, **self._fila_catalogo(self._filas[ref], fila))
        self.cambiado.emit()

    @Property(int, notify=cambiado)
    def total(self) -> int:
        return len(self._filas)

    @Property("QVariantMap", notify=cambiado)
    def contadores(self) -> dict:
        c = {e: 0 for e, _t in ver.ESTADOS}
        for f in self._tabla.todas():
            c[f["clave"]] = c.get(f["clave"], 0) + 1
        return c

    @Property(str, notify=cambiado)
    def resumen(self) -> str:
        c = self.contadores
        d = self._catalogo.get("disciplinas", [])
        return (f"{len(self._filas)} modelos · {len(d)} disciplina{'s' if len(d) != 1 else ''} · {c.get('verificado', 0)} verificados · "
                f"{c.get('diferencias', 0)} con diferencias · {c.get('sin_verificar', 0)} sin verificar")

    @Property("QVariantList", notify=cambiado)
    def filasDisciplinas(self) -> list:
        filas = [{"nombre": "disciplina", "texto": "Todas", "icono": "view-list-tree", "contador": len(self._filas)}]
        for d in self._catalogo.get("disciplinas", []):
            n = sum(1 for f in self._filas.values() if f["disciplina"] == d)
            filas.append({"nombre": f"disciplina.{d}", "texto": lab.nombre_de(d), "icono": lab.icono_de(d), "contador": n})
        return filas

    @Property("QVariantList", notify=cambiado)
    def filasEstados(self) -> list:
        c = self.contadores
        iconos = {"verificado": "data-success", "diferencias": "data-error", "sin_verificar": "data-information"}
        return [{"nombre": f"estado.{e}", "texto": t, "icono": iconos[e], "contador": c.get(e, 0)} for e, t in ver.ESTADOS]

    @Property("QVariantList", notify=cambiado)
    def refs(self) -> list:
        return list(self._orden)

    @Property("QVariantList", constant=True)
    def disciplinas(self) -> list:
        return [{"nombre": d, "texto": lab.nombre_de(d), "icono": lab.icono_de(d)} for d in self._catalogo.get("disciplinas", [])]

    # ------------------------------------------------------------------ el modelo actual
    @Slot(int)
    def fijarFila(self, fila: int) -> None:
        if fila < 0 or fila >= self._modelo.rowCount():
            return
        self._fijar_actual(self._tabla.fila(self._modelo.filaOrigen(fila)).get("ref", ""))

    @Slot(str, result=int)
    def filaDe(self, ref: str) -> int:
        for i, f in enumerate(self._tabla.todas()):
            if f.get("ref") == ref:
                return self._modelo.filaVisible(i)
        return -1

    @Slot(str, result=bool)
    def irA(self, ref: str) -> bool:
        """Selecciona el modelo en la tabla (quita los filtros si lo ocultan): la paleta."""
        if ref not in self._filas:
            return False
        if self.filaDe(ref) < 0:
            self.espacio.fijarEstado("")
            self.espacio.fijarDisciplina("")
        self._fijar_actual(ref)
        self.seleccionar.emit(self.filaDe(ref))
        return True

    def _fijar_actual(self, ref: str) -> None:
        if ref == self._actual:
            return
        self._actual = ref if ref in self._filas else ""
        self._m, self._archivo, self._motivo, self._ficha, self._figura = None, None, "", "", ""
        self._valores, self._escenario, self._corrida, self._grafico, self._registro = {}, "base", {}, {}, ""
        self._base, self._grafico_base, self._sens, self._vivo_modelo = {}, {}, {}, True
        self._resultados.poner([])
        self._verificaciones.poner([])
        if self._actual:
            f = self._filas[self._actual]
            try:
                self._m = self.lab.modelo(f["disciplina"], f["id"])
                self._archivo = self.lab.archivo(f["disciplina"], f["id"])
            except Exception as e:      # noqa: BLE001  un modelo roto no tumba la ventana
                self._motivo = f"{type(e).__name__}: {e}"
                self.consola.registrar("error", f"No se pudo importar {self._actual}: {self._motivo}")
            if self._m is not None:
                self._valores = dict(self._m.dict_params())
                self._propios = self._leer_propios()
                self._ficha = self._armar_ficha()
                self._leer_corrida()
                self._leer_verificaciones()
        self.actualCambiado.emit()
        if self._m is not None:
            self._sens_param = self._sens_param if self._sens_param in self._valores else (self._m.parametros[0].nombre if self._m.parametros else "")
            self._sens_magnitud = ""
            if self.verificar_al_abrir and self.estado == "sin_verificar":
                self.verificar()
            self.correr(en_vivo=True)
        self.valoresCambiados.emit()
        self.corridaCambiada.emit()
        self.verificacionCambiada.emit()
        self.figuraCambiada.emit()

    def _fila_actual(self) -> dict:
        return self._filas.get(self._actual, {})

    @Property(bool, notify=actualCambiado)
    def hayActual(self) -> bool:
        return bool(self._actual)

    @Property(bool, notify=actualCambiado)
    def cargado(self) -> bool:
        return self._m is not None

    @Property(str, notify=actualCambiado)
    def motivoNoCargado(self) -> str:
        return self._motivo

    @Property(str, notify=actualCambiado)
    def ref(self) -> str:
        return self._actual

    @Property(str, notify=actualCambiado)
    def id(self) -> str:
        return self._fila_actual().get("id", "")

    @Property(str, notify=actualCambiado)
    def titulo(self) -> str:
        return self._fila_actual().get("titulo", "")

    @Property(str, notify=actualCambiado)
    def disciplina(self) -> str:
        return self._fila_actual().get("disciplina", "")

    @Property(str, notify=actualCambiado)
    def textoDisciplina(self) -> str:
        return lab.nombre_de(self.disciplina) if self._actual else ""

    @Property(str, notify=actualCambiado)
    def seccion(self) -> str:
        return self._fila_actual().get("seccion") or ""

    @Property(str, notify=actualCambiado)
    def pregunta(self) -> str:
        return (self._fila_actual().get("ficha") or {}).get("pregunta", "")

    @Property(str, notify=actualCambiado)
    def archivo(self) -> str:
        return str(self._archivo) if self._archivo else (str(self.raiz / self._fila_actual()["archivo"]) if self._actual and self._fila_actual().get("archivo") else "")

    @Property(str, notify=actualCambiado)
    def archivoCorto(self) -> str:
        return self._fila_actual().get("archivo", "")

    @Property(str, notify=actualCambiado)
    def carpetaDisciplina(self) -> str:
        return str(self.raiz / self.disciplina) if self._actual else str(self.raiz)

    @Property(str, notify=cambiado)
    def estado(self) -> str:
        return self.estados.estado(self._actual, self._archivo) if self._actual else ""

    @Property(str, notify=cambiado)
    def textoEstado(self) -> str:
        return ver.TEXTO_DE_ESTADO.get(self.estado, "")

    @Property(str, notify=cambiado)
    def nivelEstado(self) -> str:
        return ver.NIVEL_DE_ESTADO.get(self.estado, "")

    @Property(str, notify=actualCambiado)
    def ficha(self) -> str:
        return self._ficha

    def _armar_ficha(self) -> str:
        f = self._fila_actual()
        imagenes = {}
        if formulas.disponible() and self._m is not None and self._m.ficha is not None:
            for latex in [e.latex for e in self._m.ficha.ecuaciones] + list(self._m.ficha.derivacion):
                ruta = formulas.imagen(latex, self._color_texto, self._cache / "formulas")
                if ruta is not None:
                    imagenes[latex] = ruta
        try:
            por_defecto = getattr(self.lab.config(), "PROCEDENCIA_POR_DEFECTO", "")
        except KeyError:
            por_defecto = ""
        return fichas.markdown(self._m, f, por_defecto, imagenes, f.get("archivo", ""))

    @Slot(str)
    def fijarColorTexto(self, color: str) -> None:
        """El color del texto del tema (QML lo manda): las fórmulas se dibujan con él."""
        color = str(color or "").strip()
        if color and color != self._color_texto:
            self._color_texto = color
            if self._m is not None and formulas.disponible():
                self._ficha = self._armar_ficha()
                self.actualCambiado.emit()

    # ------------------------------------------------------------------ parámetros y escenario
    @Property("QVariantList", notify=actualCambiado)
    def parametros(self) -> list:
        if self._m is None:
            return []
        return [{"nombre": p.nombre, "etiqueta": p.etiqueta or p.nombre, "valor": float(p.valor), "minimo": float(p.minimo), "maximo": float(p.maximo),
                 "paso": float(p.paso or 0.1), "unidad": p.unidad, "grupo": p.grupo, "definicion": p.definicion} for p in self._m.parametros]

    @Property("QVariantMap", notify=valoresCambiados)
    def valores(self) -> dict:
        return {k: float(v) for k, v in self._valores.items()}

    @Slot(str, float)
    def fijarValor(self, nombre: str, valor: float) -> None:
        if self._m is None or nombre not in self._valores:
            return
        p = self._m.parametro(nombre)
        v = min(max(float(valor), p.minimo), p.maximo)
        if abs(v - float(self._valores[nombre])) > 1e-12:
            self._valores[nombre] = v
            if self._escenario != "propio":
                self._escenario = "propio"
            self.valoresCambiados.emit()
            if self._vivo and self._vivo_modelo:
                self._espera.start()

    @Slot()
    def restablecer(self) -> None:
        if self._m is None:
            return
        self._valores = dict(self._m.dict_params())
        self._escenario = "base"
        self.valoresCambiados.emit()
        if self._vivo and self._vivo_modelo:
            self._espera.start()

    def _escenarios_modelo(self) -> list[dict]:
        if self._m is None:
            return []
        return [{"nombre": e.nombre, "descripcion": e.descripcion, "cambios": dict(e.cambios), "lectura": e.lectura, "cadena": list(e.cadena), "propio": False}
                for e in self._m.escenarios]

    @Property("QVariantList", notify=actualCambiado)
    def escenarios(self) -> list:
        base = [{"nombre": "base", "descripcion": "la base: los valores por defecto del modelo", "cambios": {}, "lectura": "", "cadena": [], "propio": False}]
        return base + self._escenarios_modelo() + [dict(e, propio=True) for e in self._propios.values()]

    @Property(str, notify=valoresCambiados)
    def escenario(self) -> str:
        return self._escenario

    @Property(int, notify=valoresCambiados)
    def indiceEscenario(self) -> int:
        return next((i for i, e in enumerate(self.escenarios) if e["nombre"] == self._escenario), -1)

    @Property(str, notify=valoresCambiados)
    def textoEscenario(self) -> str:
        e = self._escenario_actual()
        if e is None:
            return "escenario propio (los valores de abajo)" if self._escenario == "propio" else ""
        return e["descripcion"]

    @Property(str, notify=valoresCambiados)
    def lecturaEscenario(self) -> str:
        e = self._escenario_actual()
        if e is None:
            cambios = {k: v for k, v in self._valores.items() if abs(v - float(self._m.parametro(k).valor)) > 1e-12} if self._m else {}
            return fichas.escenario_markdown({"descripcion": "escenario propio: los valores actuales de los parámetros", "cambios": cambios, "lectura": "", "cadena": []}, True)
        return fichas.escenario_markdown(e, e.get("propio", False))

    def _escenario_actual(self) -> dict | None:
        return next((e for e in self.escenarios if e["nombre"] == self._escenario), None)

    @Slot(str)
    def aplicarEscenario(self, nombre: str) -> None:
        if self._m is None:
            return
        e = next((x for x in self.escenarios if x["nombre"] == nombre), None)
        if e is None:
            return
        self._valores = dict(self._m.dict_params())
        for k, v in e["cambios"].items():
            if k in self._valores:
                self._valores[k] = float(v)
        self._escenario = nombre
        self.valoresCambiados.emit()
        if self._vivo and self._vivo_modelo:
            self._espera.start()

    @Slot(int)
    def aplicarEscenarioPorIndice(self, i: int) -> None:
        lista = self.escenarios
        if 0 <= i < len(lista):
            self.aplicarEscenario(lista[i]["nombre"])

    @Property("QVariantList", notify=actualCambiado)
    def nombresEscenarios(self) -> list:
        return [e["nombre"] for e in self._escenarios_modelo()]

    # ------------------------------------------------------------------ escenarios propios del studio
    def _archivo_propios(self) -> Path:
        return self._datos / "escenarios" / f"{self._actual.replace('/', '-')}.json"

    def _leer_propios(self) -> dict:
        try:
            datos = json.loads(self._archivo_propios().read_text(encoding="utf-8"))
            return {e["nombre"]: e for e in datos.get("escenarios", [])}
        except (OSError, ValueError, KeyError, TypeError):
            return {}

    def planGuardarEscenario(self, nombre: str) -> str:
        if self._m is None:
            return "Elige primero un modelo."
        nombre = (nombre or "").strip() or f"propio-{time.strftime('%Y%m%d-%H%M')}"
        cambios = {k: v for k, v in self._valores.items() if abs(v - float(self._m.parametro(k).valor)) > 1e-12}
        return (f"Escenario «{nombre}» de {self._actual} en {self._archivo_propios()}\n\ncambios: " + (", ".join(f"{k} = {v:g}" for k, v in cambios.items()) or "ninguno (igual a la base)")
                + "\n\nEl modelo no cambia: el escenario vive en los datos del studio y aparece en su selector.")

    def guardarEscenario(self, nombre: str) -> bool:
        if self._m is None:
            return False
        nombre = (nombre or "").strip() or f"propio-{time.strftime('%Y%m%d-%H%M')}"
        cambios = {k: v for k, v in self._valores.items() if abs(v - float(self._m.parametro(k).valor)) > 1e-12}
        self._propios[nombre] = {"nombre": nombre, "descripcion": f"{nombre} (propio del studio)", "cambios": cambios, "lectura": "", "cadena": [],
                                 "fecha": time.strftime("%Y-%m-%d %H:%M")}
        archivo = self._archivo_propios()
        try:
            archivo.parent.mkdir(parents=True, exist_ok=True)
            archivo.write_text(json.dumps({"ref": self._actual, "escenarios": list(self._propios.values())}, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError as e:
            self.aviso.emit(f"No se pudo guardar el escenario: {e}", "error")
            return False
        self._escenario = nombre
        self.consola.registrar("ok", f"Escenario «{nombre}» guardado en {archivo}")
        self.actualCambiado.emit()
        self.valoresCambiados.emit()
        return True

    # ------------------------------------------------------------------ la corrida
    def _archivo_corrida(self, ref: str) -> Path:
        return self._cache / "corridas" / f"{ref.replace('/', '-')}.json"

    def _fecha_corrida(self, ref: str) -> str:
        try:
            return json.loads(self._archivo_corrida(ref).read_text(encoding="utf-8")).get("fecha", "")
        except (OSError, ValueError):
            return ""

    def _leer_corrida(self) -> None:
        try:
            datos = json.loads(self._archivo_corrida(self._actual).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        self._corrida = datos.get("corrida", {})
        self._escenario = datos.get("escenario", "base")
        if datos.get("valores"):
            self._valores.update({k: float(v) for k, v in datos["valores"].items() if k in self._valores})
        self._registro = datos.get("registro", "")
        self._grafico = self._armar_grafico()

    def _armar_grafico(self) -> dict:
        if not self._corrida or self._m is None:
            return {}
        return sim.grafico(self._corrida.get("curvas", {}), self._m.xlabel, self._m.ylabel)

    @Slot(result=bool)
    def correr(self, en_vivo: bool = False) -> bool:
        """F5 de «Correr el escenario» (o el recálculo en vivo al mover un parámetro): el motor en proceso; la corrida
        queda en la caché del studio. En vivo no escribe en la consola; si el modelo tarda más de TOPE_VIVO_MS, el modo
        en vivo se apaga para él (L4)."""
        if self._m is None:
            if not en_vivo:
                self.aviso.emit(self._motivo or "Elige primero un modelo.", "aviso")
            return False
        self.lab.activar(self.disciplina)
        inicio = time.monotonic()
        try:
            corrida = corridas.correr(self.lab.navegador(), self._m, self._valores)
            if not self._base:
                self._base = corridas.correr(self.lab.navegador(), self._m, {})
                self._grafico_base = sim.grafico(self._base.get("curvas", {}), self._m.xlabel, self._m.ylabel)
            base = self._base
        except Exception as e:      # noqa: BLE001  un parámetro fuera de dominio no tumba la ventana
            self._registro = f"# {time.strftime('%Y-%m-%d %H:%M:%S')} · correr · {self._actual} · {self._escenario}\nNo se pudo calcular: {type(e).__name__}: {e}\n"
            self.consola.registrar("error", f"{self._actual}: no se pudo calcular: {e}")
            self.corridaCambiada.emit()
            self.aviso.emit(f"No se pudo calcular {self.id}: {e}", "error")
            return False
        segundos = time.monotonic() - inicio
        self._ms = segundos * 1000
        if en_vivo and self._ms > TOPE_VIVO_MS and self._vivo_modelo:
            self._vivo_modelo = False
            self.vivoCambiado.emit()
            self.aviso.emit(f"{self.id} tarda {self._ms:.0f} ms por cálculo: el recálculo en vivo se apaga para este modelo; corre con F5.", "informacion")
        self._corrida = corrida
        self._corrida["base"] = base.get("resultados", [])
        self._grafico = self._armar_grafico()
        filas = corridas.comparar(base.get("resultados", []), corrida.get("resultados", []))
        self._resultados.poner([dict(f, nivel={"↑": "positivo", "↓": "negativo"}.get(f["signo"], ""), habilitado=True) for f in filas])
        lineas = [f"# {time.strftime('%Y-%m-%d %H:%M:%S')} · correr · {self._actual} · escenario {self._escenario} · {segundos * 1000:.0f} ms",
                  "valores: " + ", ".join(f"{k} = {v:g}" for k, v in corrida.get("valores", {}).items()), ""]
        curvas = corrida.get("curvas", {})
        for linea in curvas.get("lineas", []):
            lineas.append(f"línea «{corridas.sin_mathtext(linea.get('etiqueta', ''))}»: {len(linea.get('x', []))} puntos")
        if curvas.get("barras"):
            lineas.append("barras: " + ", ".join(f"{c} = {v}" for c, v in zip(curvas["barras"]["categorias"], curvas["barras"]["valores"])))
        if curvas.get("equilibrio"):
            lineas.append(f"equilibrio: ({curvas['equilibrio']['x']}, {curvas['equilibrio']['y']})")
        lineas.append("")
        for f in filas:
            lineas.append(f"{f['magnitud']}: base {f['base']} → {f['escenario']} ({f['delta']}, {f['pct']})")
        self._registro = "\n".join(lineas) + "\n"
        if not en_vivo:
            for l in lineas:
                self.consola.escribir(l, "info")
        self._guardar_corrida()
        self._actualizar_fila(self._actual)
        self.corridaCambiada.emit()
        self.figuraCambiada.emit()
        return True

    def _guardar_corrida(self) -> None:
        archivo = self._archivo_corrida(self._actual)
        try:
            archivo.parent.mkdir(parents=True, exist_ok=True)
            archivo.write_text(json.dumps({"ref": self._actual, "fecha": time.strftime("%Y-%m-%d %H:%M"), "escenario": self._escenario,
                                           "valores": self._valores, "corrida": self._corrida, "registro": self._registro},
                                          ensure_ascii=False, allow_nan=False), encoding="utf-8")
        except (OSError, ValueError) as e:
            self.consola.registrar("warn", f"No se pudo guardar la corrida: {e}")

    @Property(bool, notify=corridaCambiada)
    def hayCorrida(self) -> bool:
        return bool(self._corrida)

    @Property("QVariantMap", notify=corridaCambiada)
    def grafico(self) -> dict:
        return dict(self._grafico)

    @Property(str, notify=corridaCambiada)
    def registro(self) -> str:
        return self._registro

    @Property("QVariantMap", notify=corridaCambiada)
    def graficoBase(self) -> dict:
        return dict(self._grafico_base)

    @Property("QVariantMap", notify=corridaCambiada)
    def limitesComunes(self) -> dict:
        return sim.unir_limites(self._grafico_base, self._grafico)

    @Property(bool, notify=actualCambiado)
    def temporal(self) -> bool:
        return bool(self._m is not None and sim.es_temporal(self._m.xlabel))

    @Property(float, notify=corridaCambiada)
    def msCorrida(self) -> float:
        return round(self._ms, 1)

    @Property("QVariantMap", notify=corridaCambiada)
    def validez(self) -> dict:
        r = self.estados.registro(self._actual) if self._actual else {}
        return sim.validez(self.estado, list(r.get("fallos", [])), self._corrida, int(self._grafico.get("noFinitos", 0)) if self._grafico else 0)

    def _vivo_get(self) -> bool:
        return self._vivo and self._vivo_modelo

    def _vivo_set(self, v: bool) -> None:
        self._vivo = bool(v)
        if v:
            self._vivo_modelo = True
        self.vivoCambiado.emit()

    vivo = Property(bool, _vivo_get, _vivo_set, notify=vivoCambiado)

    # ------------------------------------------------------------------ la sensibilidad (L6)
    @Property("QVariantList", notify=corridaCambiada)
    def magnitudes(self) -> list:
        return sim.magnitudes(self._base.get("resultados", [])) if self._base else []

    @Property(str, notify=sensibilidadCambiada)
    def parametroSensibilidad(self) -> str:
        return self._sens_param

    @Property(str, notify=sensibilidadCambiada)
    def magnitudSensibilidad(self) -> str:
        return self._sens.get("magnitud", self._sens_magnitud)

    @Property("QVariantMap", notify=sensibilidadCambiada)
    def sensibilidad(self) -> dict:
        return dict(self._sens)

    @Slot(str, str, result=bool)
    def calcularSensibilidad(self, parametro: str, magnitud: str) -> bool:
        """El barrido del parámetro sobre su rango declarado para una magnitud de los resultados (`base.sensibilidad`)."""
        if self._m is None:
            return False
        parametro = parametro or self._sens_param
        self.lab.activar(self.disciplina)
        try:
            self._sens = sim.sensibilidad(self.lab.base(), self._m, parametro, magnitud or "")
        except Exception as e:      # noqa: BLE001
            self._sens = {}
            self.aviso.emit(f"No se pudo barrer {parametro}: {e}", "error")
            self.sensibilidadCambiada.emit()
            return False
        self._sens_param, self._sens_magnitud = parametro, self._sens["magnitud"]
        self.sensibilidadCambiada.emit()
        return True

    @Property(str, notify=corridaCambiada)
    def fechaCorrida(self) -> str:
        return self._fecha_corrida(self._actual) if self._actual else ""

    @Property(int, notify=corridaCambiada)
    def nResultados(self) -> int:
        return self._resultados.filas

    def _carpeta_salidas(self) -> Path:
        return self.raiz / self.disciplina / "salidas" / "studio" / self.id

    def planDatos(self) -> str:
        if not self._corrida:
            return "No hay corrida: corre primero el escenario (F5 con «Correr el escenario»)."
        carpeta = self._carpeta_salidas()
        nombre = self._escenario or "base"
        csv = corridas.csv_series(self._corrida.get("curvas", {}))
        return (f"Escribiría en {rutas.relativa(carpeta)}/:\n  {nombre}.csv ({len(csv.splitlines())} filas)\n  {nombre}.json (la corrida entera: valores, curvas y resultados)\n\n"
                "salidas/ es regenerable y está fuera de git.")

    def escribirDatos(self) -> bool:
        if not self._corrida:
            self.aviso.emit("No hay corrida que exportar: corre primero el escenario.", "aviso")
            return False
        carpeta = self._carpeta_salidas()
        nombre = self._escenario or "base"
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
            (carpeta / f"{nombre}.csv").write_text(corridas.csv_series(self._corrida.get("curvas", {})), encoding="utf-8")
            (carpeta / f"{nombre}.json").write_text(corridas.json_corrida(self._corrida, self._actual, nombre), encoding="utf-8")
        except (OSError, ValueError) as e:
            self.aviso.emit(f"No se pudo escribir: {e}", "error")
            return False
        self.consola.registrar("ok", f"Datos de {self._actual} · {nombre} en {carpeta}")
        return True

    # ------------------------------------------------------------------ la figura académica (matplotlib)
    @Property(bool, constant=True)
    def hayMatplotlib(self) -> bool:
        return formulas.disponible()

    @Property(str, notify=figuraCambiada)
    def figura(self) -> str:
        return self._figura

    @Slot(result=bool)
    def pedirFigura(self) -> bool:
        """La figura de `graficos.figura` (fondo blanco, la paleta del laboratorio) a un PNG de la caché."""
        if self._m is None or not formulas.disponible():
            return False
        self.lab.activar(self.disciplina)
        try:
            fig = self.lab.graficos().figura(self._m, dict(self._valores))
            carpeta = self._cache / "figuras"
            carpeta.mkdir(parents=True, exist_ok=True)
            ruta = carpeta / f"{self._actual.replace('/', '-')}.png"
            fig.savefig(str(ruta), dpi=110)
        except Exception as e:      # noqa: BLE001
            self.aviso.emit(f"No se pudo dibujar la figura académica: {e}", "error")
            return False
        self._figura = ruta.as_uri() + f"?{int(time.time() * 1000)}"
        self.figuraCambiada.emit()
        return True

    # ------------------------------------------------------------------ las verificaciones
    def _archivo_verificaciones(self, ref: str) -> Path:
        return self._cache / "verificaciones" / f"{ref.replace('/', '-')}.json"

    def _leer_verificaciones(self) -> None:
        try:
            filas = json.loads(self._archivo_verificaciones(self._actual).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            filas = []
        self._verificaciones.poner(filas)

    @Slot(result=bool)
    def verificar(self) -> bool:
        """F5 de «Verificar el modelo»: `base.verificar` y las citas, en proceso; el estado queda en la caché."""
        if self._m is None:
            self.aviso.emit(self._motivo or "Elige primero un modelo.", "aviso")
            return False
        self.lab.activar(self.disciplina)
        try:
            fuentes = self.lab.fuentes()
        except Exception:       # noqa: BLE001
            fuentes = None
        try:
            procedencia = getattr(self.lab.config(), "PROCEDENCIA_POR_DEFECTO", "")
            procedencia = (self._m.ficha.procedencia if self._m.ficha is not None and self._m.ficha.procedencia else procedencia)
        except KeyError:
            procedencia = ""
        filas = ver.verificar(self.lab.base(), self._m, self._archivo, fuentes, procedencia)
        bien, total = ver.resumen(filas)
        self.estados.registrar(self._actual, self._archivo, bien, total, [f["mensaje"] for f in filas if not f["ok"]])
        self._verificaciones.poner(filas)
        try:
            archivo = self._archivo_verificaciones(self._actual)
            archivo.parent.mkdir(parents=True, exist_ok=True)
            archivo.write_text(json.dumps(filas, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
        for f in filas:
            self.consola.escribir(f"{'✔' if f['ok'] else '✘'} {self.id} {f['mensaje']}: {f['detalle']}", "ok" if f["ok"] else "error")
        self.consola.escribir(f"{bien}/{total} verificaciones superadas" + ("" if bien == total else f" — {total - bien} FALLARON"), "info")
        self._actualizar_fila(self._actual)
        self.verificacionCambiada.emit()
        self.corridaCambiada.emit()                  # la validez de la corrida depende del estado
        return bien == total

    @Property(int, notify=verificacionCambiada)
    def nVerificaciones(self) -> int:
        return self._verificaciones.filas

    @Property(int, notify=verificacionCambiada)
    def nFallos(self) -> int:
        return sum(1 for f in self._verificaciones.todas() if not f.get("ok", True))

    @Property(str, notify=verificacionCambiada)
    def fechaVerificacion(self) -> str:
        return self.estados.registro(self._actual).get("fecha", "") if self._actual else ""

    @Property(str, notify=verificacionCambiada)
    def resumenVerificacion(self) -> str:
        r = self.estados.registro(self._actual) if self._actual else {}
        if not r:
            return "Sin verificar en este studio"
        estado = self.estado
        texto = f"{r.get('bien', 0)} de {r.get('total', 0)} verificaciones superadas el {r.get('fecha', '')}"
        return texto + (" · el archivo del modelo cambió después: vuelve a verificar" if estado == "sin_verificar" else "")

    # ------------------------------------------------------------------ paleta
    def entradas_paleta(self, _texto: str) -> list[dict]:
        return [{"nombre": f"modelo.{f['ref']}", "texto": f"{f['id']} · {f['titulo']}", "grupo": lab.nombre_de(f["disciplina"]), "icono": lab.icono_de(f["disciplina"]),
                 "ejecutar": lambda r=f["ref"]: self.irA(r)} for f in self._filas.values()]
