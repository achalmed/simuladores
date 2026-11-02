"""studio/sim_app/servicios/verificaciones.py — las verificaciones de un modelo y su estado en el studio (sin Qt).

`verificar` corre `base.verificar` (la coherencia estructural más las verificaciones del modelo) y, si la ficha cita
(`Ficha.fuentes`), `fuentes.comprobar` por cita; cada fila lleva el nivel, el nombre, el detalle que el motor devuelve
(el valor, lo esperado, la diferencia), la fuente y el archivo. `Estados` guarda en la caché del studio, por modelo, el
resultado con la fecha y la huella del archivo del modelo: «verificado» (todas pasaron y el archivo no cambió), «con
diferencias» (alguna falló) o «sin verificar» (nunca, o el archivo cambió). `desde_salida_cli` lee la salida de
`main.py verificar` de una disciplina (✔/✘ por modelo) para actualizar todos sus estados de una vez."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

ESTADOS = (("verificado", "Verificado"), ("diferencias", "Con diferencias"), ("sin_verificar", "Sin verificar"))
NIVEL_DE_ESTADO = {"verificado": "positivo", "diferencias": "negativo", "sin_verificar": "neutro"}
TEXTO_DE_ESTADO = dict(ESTADOS)
_LINEA_CLI = re.compile(r"^\s*([✔✘])\s+(\S+)\s+(.*?):\s*(.*)$")
_FUENTES_NIVEL = {"verificada": "informacion", "aviso": "aviso", "falla": "error", "no_comprobable": "otro"}


def huella(archivo: Path | None) -> str:
    try:
        st = Path(archivo).stat()
        return f"{int(st.st_mtime)}:{st.st_size}"
    except (OSError, TypeError):
        return ""


def verificar(base, modelo, archivo: Path | None, fuentes=None, procedencia: str = "") -> list[dict]:
    """[{nivel, mensaje, detalle, archivo, linea, fuente, ok}] de `base.verificar` y de las citas de la ficha."""
    filas = []
    for nombre, ok, detalle in base.verificar(modelo):
        filas.append({"nivel": "informacion" if ok else "error", "mensaje": str(nombre), "detalle": str(detalle), "ok": bool(ok),
                      "archivo": Path(archivo).name if archivo else "", "linea": 0, "fuente": procedencia})
    citas = list(getattr(getattr(modelo, "ficha", None), "fuentes", None) or [])
    for f in citas:
        try:
            estado, detalle = fuentes.comprobar(f) if fuentes is not None else ("no_comprobable", "fuentes.py no disponible")
        except Exception as e:     # noqa: BLE001  una biblioteca ausente no tumba la verificación
            estado, detalle = "no_comprobable", f"{type(e).__name__}: {e}"
        estado = str(estado)
        filas.append({"nivel": _FUENTES_NIVEL.get(estado, "otro"), "mensaje": f"cita · calibre {f.calibre_id}, p. {f.pagina}" + (f" · {f.afirma}" if f.afirma else ""),
                      "detalle": f"{estado}: {detalle}", "ok": estado != "falla", "archivo": Path(archivo).name if archivo else "", "linea": 0,
                      "fuente": f"calibre_id {f.calibre_id}, hoja {f.pagina_pdf}: «{f.pasaje}»"})
    return filas


def resumen(filas: list[dict]) -> tuple[int, int]:
    """(bien, total) de las verificaciones del motor (las citas no cuentan en el estado)."""
    del_motor = [f for f in filas if not f["mensaje"].startswith("cita ·")]
    return sum(1 for f in del_motor if f["ok"]), len(del_motor)


class Estados:
    """Los estados de verificación por modelo (`ref` = disciplina/id) en `verificaciones.json` de la caché del studio."""

    def __init__(self, archivo: Path):
        self.archivo = Path(archivo)
        self._datos: dict[str, dict] = {}
        try:
            self._datos = json.loads(self.archivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self._datos = {}

    def _guardar(self) -> None:
        try:
            self.archivo.parent.mkdir(parents=True, exist_ok=True)
            self.archivo.write_text(json.dumps(self._datos, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass

    def registro(self, ref: str) -> dict:
        return self._datos.get(ref, {})

    def estado(self, ref: str, archivo: Path | None) -> str:
        r = self._datos.get(ref)
        if not r or (archivo is not None and r.get("huella") and r["huella"] != huella(archivo)):
            return "sin_verificar"
        return "verificado" if r.get("bien", 0) == r.get("total", 0) and r.get("total", 0) > 0 else "diferencias"

    def registrar(self, ref: str, archivo: Path | None, bien: int, total: int, fallos: list[str] | None = None) -> None:
        self._datos[ref] = {"fecha": time.strftime("%Y-%m-%d %H:%M"), "huella": huella(archivo), "bien": bien, "total": total,
                            "fallos": list(fallos or [])}
        self._guardar()

    def desde_salida_cli(self, disciplina: str, texto: str, archivos: dict[str, Path]) -> dict[str, tuple[int, int]]:
        """Lee «✔ m01 nombre: detalle» / «✘ …» de `main.py verificar` y registra el estado de cada modelo. Devuelve
        {ref: (bien, total)}."""
        cuenta: dict[str, list] = {}
        for linea in texto.splitlines():
            m = _LINEA_CLI.match(linea)
            if not m:
                continue
            signo, id_, nombre, _detalle = m.groups()
            c = cuenta.setdefault(id_, [0, 0, []])
            c[1] += 1
            if signo == "✔":
                c[0] += 1
            else:
                c[2].append(nombre)
        salida = {}
        for id_, (bien, total, fallos) in cuenta.items():
            ref = f"{disciplina}/{id_}"
            self.registrar(ref, archivos.get(id_), bien, total, fallos)
            salida[ref] = (bien, total)
        return salida
