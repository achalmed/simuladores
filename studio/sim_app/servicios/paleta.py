"""studio/sim_app/servicios/paleta.py — los colores del modelo llevados a la paleta del tema (reingeniería L3; sin Qt).

Los modelos colorean sus curvas y barras con colores de matplotlib (hex, nombres, `C0`–`C9`, `tab:*`) que significan
algo: filtraciones en rojo, inyecciones en verde, la demanda en azul. La ventana no pinta esos hex (romperían el tema
claro u oscuro): cada color se lleva a un ROL por su tono — azul, rojo, verde, dorado, morado, cian, gris o texto — y
QML pinta cada rol con un color de `Kirigami.Theme`. Así se conserva el sentido y manda el tema.
"""
from __future__ import annotations

import colorsys
import re

ROLES = ("azul", "rojo", "verde", "dorado", "morado", "cian", "gris", "texto")

# los nombres de matplotlib más usados (lo demás cae por su hex o por el orden)
_NOMBRES = {
    "blue": "#1f77b4", "red": "#d62728", "green": "#2ca02c", "orange": "#ff7f0e", "purple": "#9467bd", "brown": "#8c564b",
    "pink": "#e377c2", "gray": "#7f7f7f", "grey": "#7f7f7f", "olive": "#bcbd22", "cyan": "#17becf", "black": "#000000",
    "white": "#ffffff", "navy": "#000080", "darkblue": "#00008b", "steelblue": "#4682b4", "royalblue": "#4169e1",
    "darkred": "#8b0000", "crimson": "#dc143c", "firebrick": "#b22222", "darkgreen": "#006400", "forestgreen": "#228b22",
    "seagreen": "#2e8b57", "teal": "#008080", "gold": "#ffd700", "goldenrod": "#daa520", "darkorange": "#ff8c00",
    "magenta": "#ff00ff", "violet": "#ee82ee", "indigo": "#4b0082", "silver": "#c0c0c0", "lightgray": "#d3d3d3",
    "darkgray": "#a9a9a9", "dimgray": "#696969", "tomato": "#ff6347", "coral": "#ff7f50", "salmon": "#fa8072",
    "b": "#1f77b4", "r": "#d62728", "g": "#2ca02c", "c": "#17becf", "m": "#9467bd", "y": "#bcbd22", "k": "#000000", "w": "#ffffff",
}
_TAB10 = ("#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf")
_HEX = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")


def _a_hex(color: str) -> str | None:
    c = str(color or "").strip().lower()
    if not c:
        return None
    if c.startswith("tab:"):
        c = c[4:]
    if re.fullmatch(r"c\d", c):
        return _TAB10[int(c[1]) % 10]
    if c in _NOMBRES:
        return _NOMBRES[c]
    m = _HEX.match(c)
    if m:
        h = m.group(1)
        return "#" + ("".join(ch * 2 for ch in h) if len(h) == 3 else h)
    return None


def rol(color, orden: int = 0) -> str:
    """El rol del tema para un color del modelo; sin color reconocible, uno por orden (para que dos series no coincidan)."""
    h = _a_hex(color)
    if h is None:
        return ROLES[orden % 6]
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    tono, luz, saturacion = colorsys.rgb_to_hls(r, g, b)
    if saturacion < 0.18 or luz < 0.08 or luz > 0.93:
        return "texto" if luz < 0.35 else "gris"
    grados = tono * 360
    if grados < 15 or grados >= 340:
        return "rojo"
    if grados < 65:
        return "dorado"
    if grados < 165:
        return "verde"
    if grados < 200:
        return "cian"
    if grados < 255:
        return "azul"
    return "morado"


def roles(colores: list, desde: int = 0) -> list[str]:
    return [rol(c, desde + i) for i, c in enumerate(colores)]
