#!/usr/bin/env python3
"""studio/medir.py — cuánto tarda cada modelo del repo en el recálculo en vivo del studio (L4): la misma corrida que hace
la ventana al mover un deslizador (`servicios.corridas.correr`: `navegador.calcular` con los valores del modelo), en
proceso, con el motor y los modelos del repo y nada más (sin datos de fuera). Una corrida de calentamiento y la mediana
de las siguientes; los que pasan del tope (`TOPE_VIVO_MS`, 400 ms) se calculan en un hilo aparte en la ventana.

    /usr/bin/python3 studio/medir.py                     # la tabla, del más lento al más rápido
    /usr/bin/python3 studio/medir.py --json tiempos.json # además, el detalle en JSON (fuera del repo)
    /usr/bin/python3 studio/medir.py --disciplina macro --repeticiones 5

Solo lee: no escribe en el repo ni en la caché del studio.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from sim_app.controladores.modelos import TOPE_VIVO_MS  # noqa: E402
from sim_app.servicios import corridas, laboratorio  # noqa: E402


def medir(lab: laboratorio.Laboratorio, disciplina: str, id_: str, repeticiones: int) -> dict:
    """{disciplina, id, ms (mediana), ms_max, error} de un modelo."""
    try:
        m = lab.modelo(disciplina, id_)
        corridas.correr(lab.navegador(), m, {})                 # calentamiento (cachés del modelo, importaciones)
        tiempos = []
        for _ in range(repeticiones):
            inicio = time.perf_counter()
            corridas.correr(lab.navegador(), m, {})
            tiempos.append((time.perf_counter() - inicio) * 1000)
        return {"disciplina": disciplina, "id": id_, "titulo": getattr(m, "nombre", "") or "", "ms": round(statistics.median(tiempos), 1),
                "ms_max": round(max(tiempos), 1), "error": ""}
    except Exception as e:      # noqa: BLE001  un modelo que no corre se anota, no corta la medición
        return {"disciplina": disciplina, "id": id_, "titulo": "", "ms": None, "ms_max": None, "error": f"{type(e).__name__}: {e}"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--disciplina", help="solo esta disciplina (macro, estadistica…)")
    ap.add_argument("--repeticiones", type=int, default=3)
    ap.add_argument("--json", help="escribe el detalle en este archivo (ruta fuera del repo)")
    a = ap.parse_args(argv)
    lab = laboratorio.Laboratorio()
    filas = []
    for d in laboratorio.disciplinas(lab.raiz):
        if a.disciplina and d != a.disciplina:
            continue
        lab.activar(d)
        for id_ in sorted(lab._modelos[d]):
            filas.append(medir(lab, d, id_, max(1, a.repeticiones)))
    filas.sort(key=lambda f: -(f["ms"] or 0))
    lentos = [f for f in filas if f["ms"] is not None and f["ms"] > TOPE_VIVO_MS]
    fallan = [f for f in filas if f["error"]]
    print(f"{len(filas)} modelos · {len(lentos)} pasan de {TOPE_VIVO_MS} ms · {len(fallan)} no corren con sus valores por omisión")
    for f in filas:
        marca = "LENTO" if f in lentos else ("ERROR" if f["error"] else "")
        valor = f"{f['ms']:8.1f} ms (máx. {f['ms_max']:.1f})" if f["ms"] is not None else "       —"
        print(f"{marca:5} {f['disciplina']:12} {f['id']:6} {valor}  {f['error']}")
    if a.json:
        Path(a.json).write_text(json.dumps({"tope_ms": TOPE_VIVO_MS, "fecha": time.strftime("%Y-%m-%d %H:%M"), "modelos": filas},
                                           ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
