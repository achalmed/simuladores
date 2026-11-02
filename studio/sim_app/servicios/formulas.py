"""studio/sim_app/servicios/formulas.py — una ecuación LaTeX dibujada con mathtext (la tipografía de las figuras) a un
PNG de la caché del studio, como hacía la ventana 1.x; None si no hay matplotlib o mathtext no la entiende (la ficha
muestra entonces el LaTeX). Sin Qt."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

# Lo que LaTeX acepta y mathtext no: se traduce a lo equivalente que sí dibuja
_A_MATHTEXT = ((r"\tfrac", r"\frac"), (r"\dfrac", r"\frac"), (r"\operatorname{", r"\mathrm{"),
               (r"\left", ""), (r"\right", ""), (r"\displaystyle", ""), (r"\big", ""), (r"\Big", ""),
               (r"\le ", r"\leq "), (r"\ge ", r"\geq "), (r"\lvert", "|"), (r"\rvert", "|"))


def disponible() -> bool:
    import importlib.util
    spec = importlib.util.find_spec("matplotlib")
    return spec is not None and spec.origin is not None       # el matplotlib vacío de navegador.py no tiene origen


def preparar(latex: str) -> str:
    latex = re.sub(r"\\text\{([^{}]*)\}", lambda m: r"\mathrm{" + m.group(1).replace(" ", r"\ ") + "}", latex)
    latex = re.sub(r"\\sqrt\s*([A-Za-z0-9])", r"\\sqrt{\1}", latex)
    for de, a in _A_MATHTEXT:
        latex = latex.replace(de, a)
    return latex


def imagen(latex: str, color: str, carpeta: Path, tam: float = 13, dpi: int = 150) -> Path | None:
    """El PNG de la ecuación con el color de texto dado (uno por latex, color y tamaño; se reutiliza)."""
    if not disponible():
        return None
    carpeta = Path(carpeta)
    clave = hashlib.sha1(f"{latex}|{color}|{tam}|{dpi}".encode("utf-8")).hexdigest()[:20]
    ruta = carpeta / f"{clave}.png"
    if ruta.is_file():
        return ruta
    try:
        from matplotlib import mathtext
        from matplotlib.font_manager import FontProperties
        carpeta.mkdir(parents=True, exist_ok=True)
        mathtext.math_to_image(f"${preparar(latex)}$", str(ruta), prop=FontProperties(size=tam, math_fontfamily="stix"), dpi=dpi,
                               format="png", color=color)
    except Exception:       # noqa: BLE001  una ecuación que mathtext no entiende se muestra como texto
        try:
            ruta.unlink()
        except OSError:
            pass
        return None
    return ruta
