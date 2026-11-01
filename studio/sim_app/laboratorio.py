"""El laboratorio dentro de Simuladores Studio (sin Qt): el catálogo y las disciplinas cargadas a demanda.

Cada disciplina (macro, estadistica…) trae su propio `config` y su propio paquete `modelos`, con los mismos nombres:
no pueden estar las dos en `sys.modules` a la vez. `Laboratorio.activar(disciplina)` guarda los módulos de la activa,
pone los de la pedida (importándolos la primera vez, como `main._cargar`) y deja `sys.path` como lo espera su
`main.py`. Las páginas navegan con `catalogo.json` (generado, el mismo que leen los pubs) y solo importan un modelo al
abrirlo. Un modelo se calcula siempre con su disciplina activa: algunos importan un auxiliar dentro de la función.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]            # simuladores/
AJENOS = ("config", "base", "graficos", "laboratorio", "reporte", "fuentes", "app", "modelos")
NOMBRES = {"macro": "Macroeconomía", "estadistica": "Estadística", "econometria": "Econometría",
           "micro": "Microeconomía", "mate": "Matemáticas"}


def catalogo() -> dict:
    return json.loads((RAIZ / "catalogo.json").read_text(encoding="utf-8"))


def disciplinas() -> list[str]:
    return sorted(d.name for d in RAIZ.iterdir()
                  if d.is_dir() and (d / "config.py").is_file() and (d / "modelos").is_dir())


def _propios(nombre: str) -> bool:
    return nombre in AJENOS or nombre.startswith("modelos.")


class Laboratorio:
    def __init__(self) -> None:
        self.activa: str | None = None
        self._guardados: dict[str, dict] = {}
        self._modelos: dict[str, dict[str, object]] = {}     # disciplina → {id: Modelo}
        self._path_base = [p for p in sys.path if p not in {str(RAIZ / d) for d in disciplinas()} | {str(RAIZ)}]

    def activar(self, disciplina: str) -> None:
        if disciplina == self.activa:
            return
        actuales = {n: sys.modules.pop(n) for n in list(sys.modules) if _propios(n)}
        if self.activa:
            self._guardados[self.activa] = actuales
        sys.path[:] = [str(RAIZ / disciplina), str(RAIZ)] + self._path_base
        self.activa = disciplina
        if disciplina in self._guardados:
            sys.modules.update(self._guardados[disciplina])
            return
        importlib.import_module("config")
        importlib.import_module("graficos")              # aplica el estilo académico de la disciplina
        modelos = {}
        carpeta = RAIZ / disciplina / "modelos"
        for f in sorted(carpeta.rglob("*.py")):
            if f.stem.startswith("_"):
                continue
            nombre = ".".join(("modelos",) + f.relative_to(carpeta).with_suffix("").parts)
            m = getattr(importlib.import_module(nombre), "MODELO", None)
            if m is not None:
                modelos[m.id or f.stem.split("_")[0]] = m
        self._modelos[disciplina] = modelos

    def modelo(self, disciplina: str, id: str):
        self.activar(disciplina)
        return self._modelos[disciplina][id]

    def graficos(self):
        """El módulo de dibujo de la disciplina activa (lleva su `config` y su estilo)."""
        return sys.modules["graficos"]

    def config(self):
        return sys.modules["config"]
