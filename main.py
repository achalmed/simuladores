#!/usr/bin/env python3
"""simuladores/main.py — el laboratorio entero: catálogo de modelos para los consumidores y verificación de todas las disciplinas.

Objetivo: dar a los pubs (y a quien no corre Python del laboratorio) un contrato estable, `catalogo.json`, con cada
  modelo de cada disciplina: id, título, área y nivel, parámetros, escenarios y la ficha resumida.
Método: cada disciplina (`<carpeta>/config.py` + `<carpeta>/modelos/`) se carga con `sys.path` y `sys.modules`
  aislados, como hace `divulgacion/lib/simuladores.py`: las disciplinas comparten nombres (`config`, `modelos`).
  El JSON es determinista (orden fijo, sin fecha) para que `catalogo --verificar` detecte un catálogo desfasado.
Uso:
  python3 main.py catalogo                 # imprime el catálogo (simula: no escribe nada)
  python3 main.py catalogo --aplicar       # escribe catalogo.json en la raíz del repo
  python3 main.py catalogo --verificar     # 0 si catalogo.json está al día · 1 si está desfasado o falta
  python3 main.py verificar                # `main.py verificar` de cada disciplina (salida 0 solo si todas pasan)
Límite: el catálogo describe los modelos, no los ejecuta; las cifras de un escenario se calculan con el modelo.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")      # las disciplinas importan matplotlib en su config: sin pantalla

RAIZ = Path(__file__).resolve().parent
CATALOGO = RAIZ / "catalogo.json"
ESQUEMA = 1                                       # versión del contrato de catalogo.json (sube si cambia un campo)
_AJENOS = ("config", "base", "graficos", "laboratorio", "reporte", "fuentes", "app", "modelos")


def disciplinas() -> list[Path]:
    """Carpetas con `config.py`, `main.py` y `modelos/`: cada una es una disciplina (macro, estadistica…)."""
    return sorted(d for d in RAIZ.iterdir()
                  if d.is_dir() and (d / "config.py").is_file() and (d / "main.py").is_file() and (d / "modelos").is_dir())


def _cargar(disc: Path):
    """(config, [Modelo]) de una disciplina, importados en un espacio de nombres aislado."""
    guardados = {n: sys.modules.pop(n) for n in list(sys.modules) if n in _AJENOS or n.startswith("modelos.")}
    path_antes = list(sys.path)
    try:
        sys.path[:0] = [str(disc), str(RAIZ)]
        config = importlib.import_module("config")
        modelos = []
        for f in sorted((disc / "modelos").rglob("*.py")):
            if f.stem.startswith("_"):
                continue
            nombre = ".".join(("modelos",) + f.relative_to(disc / "modelos").with_suffix("").parts)
            m = getattr(importlib.import_module(nombre), "MODELO", None)
            if m is not None:
                modelos.append((m, f))
        return config, modelos
    finally:
        for n in [n for n in sys.modules if n in _AJENOS or n.startswith("modelos.")]:
            sys.modules.pop(n)
        sys.modules.update(guardados)
        sys.path[:] = path_antes


def _cursos(disc: Path) -> dict[str, list[dict]]:
    """{id del modelo: [{curso, tema}]} desde `<disciplina>/temario.yml`, si la disciplina lo tiene."""
    t = disc / "temario.yml"
    if not t.is_file():
        return {}
    import yaml
    datos = yaml.safe_load(t.read_text(encoding="utf-8")) or {}
    return {tema["id"]: [{"curso": c["curso"], "tema": str(c["tema"])} for c in tema.get("cursos", [])]
            for sec in datos.get("secciones", []) for tema in sec.get("temas", []) if tema.get("cursos")}


def _ficha(m, por_defecto: str) -> dict:
    f = m.ficha
    if f is None:
        return {}
    return {
        "pregunta": f.pregunta,
        "autores": f.autores,
        "intuicion": f.intuicion,
        "supuestos": list(f.supuestos),
        "ecuaciones": [{"nombre": e.nombre, "latex": e.latex} for e in f.ecuaciones],
        "procedencia": f.procedencia or por_defecto,
        "fuentes": [{"calibre_id": x.calibre_id, "pagina": x.pagina} for x in f.fuentes],
    }


def catalogo() -> dict:
    modelos = []
    for disc in disciplinas():
        config, lista = _cargar(disc)
        cursos = _cursos(disc)
        secciones = getattr(config, "SECCIONES", {})
        por_defecto = getattr(config, "PROCEDENCIA_POR_DEFECTO", "")
        for m, archivo in lista:
            modelos.append({
                "id": m.id,
                "disciplina": disc.name,
                "ref": f"{disc.name}/{m.id}",               # la referencia que usa divulgacion (`simuladores: [macro/m04]`)
                "titulo": m.nombre,
                "area": getattr(config, "AREA", None),
                "nivel": m.nivel,
                "seccion": secciones.get(m.nivel),
                "archivo": archivo.relative_to(RAIZ).as_posix(),
                "parametros": [{"nombre": p.nombre, "etiqueta": p.etiqueta, "valor": p.valor, "minimo": p.minimo,
                                "maximo": p.maximo, "paso": p.paso, "unidad": p.unidad, "grupo": p.grupo,
                                "definicion": p.definicion} for p in m.parametros],
                "escenarios": [{"nombre": e.nombre, "descripcion": e.descripcion} for e in m.escenarios],
                "verificaciones": len(m.verificaciones),
                "ficha": _ficha(m, por_defecto),
                "cursos": cursos.get(m.id, []),
            })
    modelos.sort(key=lambda x: (x["disciplina"], x["nivel"] or 99, x["id"]))
    return {
        "_generado": "GENERADO por simuladores/main.py catalogo --aplicar; no editar",
        "esquema": ESQUEMA,
        "disciplinas": sorted({x["disciplina"] for x in modelos}),
        "total": len(modelos),
        "modelos": modelos,
    }


def _texto(c: dict) -> str:
    return json.dumps(c, ensure_ascii=False, indent=1, allow_nan=False) + "\n"   # JSON estricto: un NaN fallaría aquí


def cmd_catalogo(a) -> int:
    texto = _texto(catalogo())
    if a.verificar:
        al_dia = CATALOGO.is_file() and CATALOGO.read_text(encoding="utf-8") == texto
        print(f"catalogo.json {'al día' if al_dia else 'desfasado o ausente (main.py catalogo --aplicar)'}")
        return 0 if al_dia else 1
    if a.aplicar:
        CATALOGO.write_text(texto, encoding="utf-8")
        n = json.loads(texto)["total"]
        print(f"[catalogo] {n} modelos → {CATALOGO.relative_to(RAIZ)}", file=sys.stderr)
        return 0
    sys.stdout.write(texto)
    print("[catalogo] SIMULACIÓN: no se escribió nada (usa --aplicar para escribir catalogo.json)", file=sys.stderr)
    return 0


def cmd_verificar(a) -> int:
    fallos = 0
    for disc in disciplinas():
        r = subprocess.run([sys.executable, "main.py", "verificar"], cwd=disc, capture_output=True, text=True)
        ultima = next((l for l in reversed(r.stdout.splitlines()) if "verificaciones superadas" in l), r.stdout.strip()[-200:])
        print(f"{'✔' if r.returncode == 0 else '✘'} {disc.name:<12} {ultima}")
        if r.returncode != 0:
            fallos += 1
            sys.stderr.write(r.stderr[-2000:])
    return 1 if fallos else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    p = sub.add_parser("catalogo", help="catálogo de modelos (catalogo.json); simula por defecto")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--aplicar", action="store_true", help="escribe catalogo.json")
    g.add_argument("--verificar", action="store_true", help="0 si catalogo.json está al día")
    sub.add_parser("verificar", help="verificar de cada disciplina")
    a = ap.parse_args()
    return {"catalogo": cmd_catalogo, "verificar": cmd_verificar}[a.orden](a)


if __name__ == "__main__":
    sys.exit(main())
