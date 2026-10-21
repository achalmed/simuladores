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
  python3 main.py web                      # qué modelos corren en el navegador (simula: no escribe nada)
  python3 main.py web --aplicar            # escribe navegador.json (archivos .py mínimos, metadatos y vista inicial)
  python3 main.py web --verificar          # 0 si navegador.json está al día · 1 si está desfasado o falta
Límite: el catálogo describe los modelos, no los ejecuta; las cifras de un escenario se calculan con el modelo.
  navegador.json no duplica ecuaciones: lista los .py que el navegador ejecuta con Pyodide (navegador.py).
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")      # las disciplinas importan matplotlib en su config: sin pantalla

RAIZ = Path(__file__).resolve().parent
CATALOGO = RAIZ / "catalogo.json"
ESQUEMA = 1                                       # versión del contrato de catalogo.json (sube si cambia un campo)
NAVEGADOR = RAIZ / "navegador.json"
ESQUEMA_WEB = 1                                   # versión del contrato de navegador.json (sube si cambia un campo)
MOTOR_WEB = ("base.py", "navegador.py")           # el motor que el navegador necesita (sin graficos/app: matplotlib)
# Lo que un modelo puede importar para correr en Pyodide: biblioteca estándar sin archivos ni procesos, numpy y el
# motor. Cualquier otra cosa (pathlib, json, glob, importlib, sys…) delata que el modelo lee datos de disco (datafw).
_IMPORTS_WEB = {"__future__", "math", "cmath", "itertools", "functools", "collections", "dataclasses", "statistics",
                "random", "typing", "numpy", "base", "config"}
PUNTOS_INICIAL = 300                              # puntos por línea en la vista inicial guardada (la figura sin Pyodide)
LENTO_WEB = 0.3                                   # segundos en CPython por cálculo: más que esto no va al navegador
                                                  # (Pyodide es 2-4 veces más lento; el más lento admitido mide 0,15 s)
_AJENOS = ("config", "base", "graficos", "laboratorio", "reporte", "fuentes", "app", "modelos")


def disciplinas() -> list[Path]:
    """Carpetas con `config.py`, `main.py` y `modelos/`: cada una es una disciplina (macro, estadistica…)."""
    return sorted(d for d in RAIZ.iterdir()
                  if d.is_dir() and (d / "config.py").is_file() and (d / "main.py").is_file() and (d / "modelos").is_dir())


def _cargar(disc: Path, dentro=None):
    """(config, [Modelo]) de una disciplina, importados en un espacio de nombres aislado.

    Si se da `dentro(config, modelos)`, se llama ANTES de restaurar el espacio de nombres: los modelos que importan
    un auxiliar dentro de una función (m32 importa `modelos.nivel_05._solow` al calcular) solo calculan ahí."""
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
        if dentro is not None:
            dentro(config, modelos)
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


# ── web: los modelos que corren en el navegador (navegador.json) ──────────────────────────────────────────────────

def _modulo_a_archivo(disc: Path, modulo: str) -> Path | None:
    """`modelos.nivel_05._solow` → <disc>/modelos/nivel_05/_solow.py (o su __init__.py si es paquete)."""
    base_ = disc.joinpath(*modulo.split("."))
    if base_.with_suffix(".py").is_file():
        return base_.with_suffix(".py")
    if (base_ / "__init__.py").is_file():
        return base_ / "__init__.py"
    return None


def _archivos_web(disc: Path, archivo: Path) -> tuple[list[str], list[str]]:
    """(archivos .py relativos a la raíz que el modelo necesita, imports que impiden correrlo en el navegador).

    Análisis estático (ast) del módulo y de los auxiliares `modelos.*` que importa, con los __init__.py de cada
    paquete; el motor (MOTOR_WEB) y el config.py de la disciplina van siempre."""
    necesarios: set[Path] = set()
    vetados: set[str] = set()
    pendientes = [archivo]
    while pendientes:
        f = pendientes.pop()
        if f in necesarios:
            continue
        necesarios.add(f)
        rel = f.relative_to(disc)
        for i in range(1, len(rel.parts)):                         # __init__.py de cada paquete del camino
            ini = disc.joinpath(*rel.parts[:i]) / "__init__.py"
            if ini.is_file() and ini not in necesarios:
                pendientes.append(ini)
        for nodo in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.Import):
                nombres = [a.name for a in nodo.names]
                subs = []
            elif isinstance(nodo, ast.ImportFrom) and nodo.module and not nodo.level:
                nombres = [nodo.module]
                subs = [f"{nodo.module}.{a.name}" for a in nodo.names]
            else:
                continue
            for nombre in nombres:
                raiz = nombre.split(".")[0]
                if raiz == "modelos":
                    for m in [nombre, *subs]:
                        destino = _modulo_a_archivo(disc, m)
                        if destino is not None:
                            pendientes.append(destino)
                elif raiz not in _IMPORTS_WEB:
                    vetados.add(nombre)
    archivos = [*MOTOR_WEB, f"{disc.name}/config.py"]
    archivos += sorted(p.relative_to(RAIZ).as_posix() for p in necesarios)
    return archivos, sorted(vetados)


def _ficha_web(m, por_defecto: str) -> dict:
    f = m.ficha
    if f is None:
        return {}
    return {
        "pregunta": f.pregunta, "contexto": f.contexto, "autores": f.autores, "supuestos": list(f.supuestos),
        "ecuaciones": [{"nombre": e.nombre, "latex": e.latex, "significado": e.significado} for e in f.ecuaciones],
        "intuicion": f.intuicion, "limitaciones": list(f.limitaciones), "evolucion": f.evolucion,
        "procedencia": f.procedencia or por_defecto,
        "fuentes": [{"calibre_id": x.calibre_id, "pagina": x.pagina, "afirma": x.afirma} for x in f.fuentes],
    }


def navegador() -> tuple[dict, list[dict]]:
    """(contenido de navegador.json, tiempos por modelo). Los tiempos no se escriben: el JSON es determinista."""
    import navegador as nav
    nav.preparar(forzar=True)                      # el mismo entorno que Pyodide: config.py con matplotlib vacío
    modelos, fuera, tiempos = [], [], []
    for disc in disciplinas():
        _cargar(disc, lambda config, lista: _web_disciplina(disc, config, lista, nav, modelos, fuera, tiempos))
    modelos.sort(key=lambda x: (x["disciplina"], x["nivel"] or 99, x["id"]))
    fuera.sort(key=lambda x: x["ref"])
    return {
        "_generado": "GENERADO por simuladores/main.py web --aplicar; no editar",
        "esquema": ESQUEMA_WEB,
        "motor": list(MOTOR_WEB),
        "requiere": ["numpy"],
        "total": len(modelos),
        "modelos": modelos,
        "fuera": fuera,
    }, tiempos


def _web_disciplina(disc: Path, config, lista, nav, modelos: list, fuera: list, tiempos: list) -> None:
    """Clasifica los modelos de una disciplina (corre / fuera, con motivo) y arma su entrada de navegador.json."""
    secciones = getattr(config, "SECCIONES", {})
    por_defecto = getattr(config, "PROCEDENCIA_POR_DEFECTO", "")
    for m, archivo in lista:
        ref = f"{disc.name}/{m.id}"
        archivos, vetados = _archivos_web(disc, archivo)
        if vetados:
            fuera.append({"ref": ref, "titulo": m.nombre,
                          "motivo": f"lee archivos o datos (datafw): importa {', '.join(vetados)}"})
            continue
        try:
            t_inicial = float("inf")
            for _ in range(3):                    # tiempo de CPU, el menor de tres: la carga de la máquina no decide
                t0 = time.process_time()
                inicial = nav.calcular(m, {}, cifras=4, max_puntos=PUNTOS_INICIAL)
                t_inicial = min(t_inicial, time.process_time() - t0)
                if t_inicial < LENTO_WEB / 3:
                    break
            for e in m.escenarios:
                nav.calcular(m, e.cambios, cifras=4)
            json.dumps(inicial, allow_nan=False)
        except Exception as exc:                # noqa: BLE001 — cualquier fallo deja el modelo fuera, con su motivo
            fuera.append({"ref": ref, "titulo": m.nombre, "motivo": f"el cálculo falla sin matplotlib: {exc}"})
            continue
        tiempos.append({"ref": ref, "segundos": t_inicial})
        if t_inicial > LENTO_WEB:
            fuera.append({"ref": ref, "titulo": m.nombre,
                          "motivo": f"cálculo lento para el navegador (más de {LENTO_WEB} s de CPU en CPython)"})
            continue
        rel = archivo.relative_to(disc).with_suffix("")
        modelos.append({
            "id": m.id, "ref": ref, "disciplina": disc.name, "titulo": m.nombre, "nivel": m.nivel,
            "seccion": secciones.get(m.nivel),
            "modulo": ".".join(rel.parts), "archivo": archivo.relative_to(RAIZ).as_posix(), "archivos": archivos,
            "xlabel": m.xlabel, "ylabel": m.ylabel, "notas": m.notas,
            "parametros": [{"nombre": p.nombre, "etiqueta": p.etiqueta, "valor": p.valor, "minimo": p.minimo,
                            "maximo": p.maximo, "paso": p.paso, "unidad": p.unidad, "grupo": p.grupo,
                            "definicion": p.definicion} for p in m.parametros],
            "escenarios": [{"nombre": e.nombre, "descripcion": e.descripcion, "cambios": e.cambios,
                            "lectura": e.lectura, "cadena": list(e.cadena)} for e in m.escenarios],
            "series": [x["etiqueta"] for x in inicial["curvas"].get("lineas", [])],
            "verificaciones": len(m.verificaciones),
            "ficha": _ficha_web(m, por_defecto),
            "inicial": inicial,
        })


def _texto_web(c: dict) -> str:
    """JSON estricto con un modelo por línea: compacto (las curvas de la vista inicial son largas) y con diffs legibles."""
    def uno(v):
        return json.dumps(v, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    filas = []
    for k, v in c.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            filas.append(f"{uno(k)}:[\n" + ",\n".join(uno(x) for x in v) + "\n]")
        else:
            filas.append(f"{uno(k)}:{uno(v)}")
    return "{\n" + ",\n".join(filas) + "\n}\n"


def cmd_web(a) -> int:
    contenido, tiempos = navegador()
    texto = _texto_web(contenido)
    if a.verificar:
        al_dia = NAVEGADOR.is_file() and NAVEGADOR.read_text(encoding="utf-8") == texto
        print(f"navegador.json {'al día' if al_dia else 'desfasado o ausente (main.py web --aplicar)'}")
        return 0 if al_dia else 1
    por_disc: dict[str, int] = {}
    for m in contenido["modelos"]:
        por_disc[m["disciplina"]] = por_disc.get(m["disciplina"], 0) + 1
    print(f"[web] {contenido['total']} modelos corren en el navegador "
          f"({', '.join(f'{d}: {n}' for d, n in sorted(por_disc.items()))}); {len(contenido['fuera'])} fuera:")
    for x in contenido["fuera"]:
        print(f"  ✘ {x['ref']:<16} {x['motivo']}")
    lentos = sorted(tiempos, key=lambda x: -x["segundos"])[:3]
    print("[web] cálculos más lentos en CPython: " + ", ".join(f"{x['ref']} {x['segundos'] * 1000:.0f} ms" for x in lentos))
    if a.aplicar:
        NAVEGADOR.write_text(texto, encoding="utf-8")
        print(f"[web] → {NAVEGADOR.relative_to(RAIZ)} ({len(texto.encode()) / 1024:.0f} KB)", file=sys.stderr)
    else:
        print("[web] SIMULACIÓN: no se escribió nada (usa --aplicar para escribir navegador.json)", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    p = sub.add_parser("catalogo", help="catálogo de modelos (catalogo.json); simula por defecto")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--aplicar", action="store_true", help="escribe catalogo.json")
    g.add_argument("--verificar", action="store_true", help="0 si catalogo.json está al día")
    sub.add_parser("verificar", help="verificar de cada disciplina")
    p = sub.add_parser("web", help="modelos que corren en el navegador (navegador.json); simula por defecto")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--aplicar", action="store_true", help="escribe navegador.json")
    g.add_argument("--verificar", action="store_true", help="0 si navegador.json está al día")
    a = ap.parse_args()
    return {"catalogo": cmd_catalogo, "verificar": cmd_verificar, "web": cmd_web}[a.orden](a)


if __name__ == "__main__":
    sys.exit(main())
