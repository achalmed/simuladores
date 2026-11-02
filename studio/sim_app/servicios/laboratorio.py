"""studio/sim_app/servicios/laboratorio.py — el laboratorio dentro de Simuladores Studio (sin Qt): el catálogo y las
disciplinas cargadas a demanda.

Cada disciplina (macro, estadistica…) trae su propio `config` y su propio paquete `modelos`, con los mismos nombres:
no pueden estar las dos en `sys.modules` a la vez. `Laboratorio.activar(disciplina)` guarda los módulos de la activa,
pone los de la pedida (importándolos la primera vez, como `main._cargar`) y deja `sys.path` como lo espera su
`main.py`. La ventana navega con `catalogo.json` (generado, el mismo que leen los pubs) y solo importa un modelo al
elegirlo. Un modelo se calcula siempre con su disciplina activa: algunos importan un auxiliar dentro de la función.
Antes de importar nada se llama a `navegador.preparar()`: si falta `matplotlib` (el Python del sistema no lo trae)
registra uno vacío, como hace el navegador de los pubs, y los `config.py` que lo importan cargan igual; `graficos`
(la figura académica) solo se importa cuando se pide, con el `matplotlib` de verdad."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from sim_app.servicios import rutas

AJENOS = ("config", "base", "graficos", "laboratorio", "reporte", "fuentes", "app", "navegador", "modelos")
NOMBRES = {"macro": "Macroeconomía", "estadistica": "Estadística", "econometria": "Econometría",
           "micro": "Microeconomía", "mate": "Matemáticas", "demo": "Demostración"}
ICONOS = {"macro": "office-chart-line", "estadistica": "office-chart-bar", "econometria": "office-chart-scatter",
          "micro": "office-chart-area", "mate": "accessories-calculator", "demo": "applications-education"}


def nombre_de(disciplina: str) -> str:
    return NOMBRES.get(disciplina, disciplina.capitalize())


def icono_de(disciplina: str) -> str:
    return ICONOS.get(disciplina, "office-chart-line")


def catalogo(raiz: Path | None = None) -> dict:
    """`catalogo.json` de la raíz (GENERADO por `main.py catalogo --aplicar`); vacío si no existe."""
    archivo = (raiz or rutas.raiz()) / "catalogo.json"
    if not archivo.is_file():
        return {"esquema": 0, "disciplinas": [], "total": 0, "modelos": []}
    return json.loads(archivo.read_text(encoding="utf-8"))


def disciplinas(raiz: Path | None = None) -> list[str]:
    r = raiz or rutas.raiz()
    return sorted(d.name for d in r.iterdir()
                  if d.is_dir() and (d / "config.py").is_file() and (d / "modelos").is_dir())


def _propios(nombre: str) -> bool:
    return nombre in AJENOS or nombre.startswith("modelos.")


class Laboratorio:
    def __init__(self, raiz: Path | None = None) -> None:
        self.raiz = raiz or rutas.raiz()
        self.activa: str | None = None
        self._guardados: dict[str, dict] = {}
        self._modelos: dict[str, dict[str, object]] = {}     # disciplina → {id: Modelo}
        self._archivos: dict[str, dict[str, Path]] = {}      # disciplina → {id: archivo}
        propias = {str(self.raiz / d) for d in disciplinas(self.raiz)} | {str(self.raiz)}
        self._path_base = [p for p in sys.path if p not in propias]

    def activar(self, disciplina: str) -> None:
        if disciplina == self.activa:
            return
        actuales = {n: sys.modules.pop(n) for n in list(sys.modules) if _propios(n)}
        if self.activa:
            self._guardados[self.activa] = actuales
        sys.path[:] = [str(self.raiz / disciplina), str(self.raiz)] + self._path_base
        self.activa = disciplina
        if disciplina in self._guardados:
            sys.modules.update(self._guardados[disciplina])
            return
        importlib.import_module("navegador").preparar()     # un matplotlib vacío si el intérprete no lo trae
        importlib.import_module("config")
        modelos, archivos = {}, {}
        carpeta = self.raiz / disciplina / "modelos"
        for f in sorted(carpeta.rglob("*.py")):
            if f.stem.startswith("_"):
                continue
            nombre = ".".join(("modelos",) + f.relative_to(carpeta).with_suffix("").parts)
            m = getattr(importlib.import_module(nombre), "MODELO", None)
            if m is not None:
                clave = m.id or f.stem.split("_")[0]
                modelos[clave] = m
                archivos[clave] = f
        self._modelos[disciplina] = modelos
        self._archivos[disciplina] = archivos

    def modelo(self, disciplina: str, id_: str):
        self.activar(disciplina)
        return self._modelos[disciplina][id_]

    def archivo(self, disciplina: str, id_: str) -> Path:
        self.activar(disciplina)
        return self._archivos[disciplina][id_]

    def config(self):
        return sys.modules["config"]

    def base(self):
        return sys.modules["base"]

    def navegador(self):
        return sys.modules["navegador"]

    def graficos(self):
        """El módulo de dibujo de la disciplina activa (lleva su `config` y su estilo): pide el matplotlib real."""
        if not rutas.hay_matplotlib():
            raise ImportError("falta matplotlib: la figura académica necesita el .venv del repo")
        return importlib.import_module("graficos")

    def fuentes(self):
        return importlib.import_module("fuentes")
