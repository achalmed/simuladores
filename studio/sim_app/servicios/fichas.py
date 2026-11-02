"""studio/sim_app/servicios/fichas.py — la ficha pedagógica de un modelo en Markdown (sin Qt), para `GuiComun.VistaTexto`:
pregunta, contexto, autores, supuestos, variables, ecuaciones (cada una con su LaTeX, dibujada con mathtext si se le
pasa su imagen, y su significado), derivación, intuición, equilibrio, limitaciones, evolución, procedencia, referencias y
fuentes. La ficha es lo que el modelo declara (`base.Ficha`): aquí no se corrige ni se completa nada."""
from __future__ import annotations

from pathlib import Path


def _lista(items) -> str:
    return "\n".join(f"- {str(i).strip()}" for i in items if str(i).strip())


def _latex(texto: str, imagen: Path | None) -> str:
    if imagen is not None:
        return f"![{texto}]({Path(imagen).as_uri()})"
    return f"`{texto}`"


def markdown(modelo, fila: dict | None = None, procedencia_por_defecto: str = "", imagenes: dict | None = None,
             archivo: str = "") -> str:
    """El Markdown de la ficha del modelo. `imagenes` = {latex: ruta del PNG} para las ecuaciones ya dibujadas."""
    imagenes = imagenes or {}
    F = getattr(modelo, "ficha", None)
    fila = fila or {}
    titulo = f"# {modelo.id} · {modelo.nombre}" if modelo.id else f"# {modelo.nombre}"
    cabecera = [titulo]
    datos = []
    if fila.get("seccion"):
        datos.append(f"**Sección**: {fila['seccion']}" + (f" (nivel {fila['nivel']})" if fila.get("nivel") else ""))
    if fila.get("area"):
        datos.append(f"**Área**: {fila['area']}")
    if archivo:
        datos.append(f"**Archivo**: `{archivo}`")
    if fila.get("cursos"):
        datos.append("**Cursos**: " + "; ".join(f"{c['curso']} · tema {c['tema']}" for c in fila["cursos"]))
    if datos:
        cabecera.append("  \n".join(datos))
    if F is None:
        return "\n\n".join(cabecera + ["Este modelo no trae ficha pedagógica."])
    partes = cabecera
    if F.pregunta:
        partes.append(f"> {F.pregunta}")
    if F.contexto:
        partes.append(f"## Contexto\n\n{F.contexto}")
    if F.autores:
        partes.append(f"## Autores\n\n{F.autores}")
    if F.supuestos:
        partes.append("## Supuestos\n\n" + _lista(F.supuestos))
    if F.variables:
        partes.append("## Variables\n\n" + "\n".join(f"- **{s}**: {d}" for s, d in F.variables))
    if F.ecuaciones:
        ecu = []
        for e in F.ecuaciones:
            ecu.append(f"**{e.nombre}**\n\n{_latex(e.latex, imagenes.get(e.latex))}\n\n{e.significado}")
        partes.append("## Ecuaciones\n\n" + "\n\n".join(ecu))
    if F.derivacion:
        partes.append("## Derivación\n\n" + "\n\n".join(_latex(p, imagenes.get(p)) for p in F.derivacion))
    if F.intuicion:
        partes.append(f"## Intuición\n\n{F.intuicion}")
    if F.equilibrio:
        partes.append(f"## Equilibrio\n\n{F.equilibrio}")
    if F.limitaciones:
        partes.append("## Limitaciones\n\n" + _lista(F.limitaciones))
    if F.evolucion:
        partes.append(f"## Lo que viene después\n\n{F.evolucion}")
    procedencia = F.procedencia or procedencia_por_defecto
    if procedencia:
        partes.append(f"## Procedencia\n\n{procedencia}")
    if F.referencias:
        partes.append("## Referencias\n\n" + _lista(F.referencias))
    if F.fuentes:
        partes.append("## Fuentes verificables\n\n" + _lista(f"calibre {f.calibre_id}, p. {f.pagina} (hoja {f.pagina_pdf}): «{f.pasaje}»" + (f" — {f.afirma}" if f.afirma else "") for f in F.fuentes))
    if modelo.notas:
        partes.append(f"## Notas de la figura\n\n{modelo.notas}")
    return "\n\n".join(partes) + "\n"


def escenario_markdown(e, propio: bool = False) -> str:
    """La lectura de un escenario: la descripción, los cambios, la lectura y el mecanismo de transmisión."""
    cambios = ", ".join(f"{k} = {v}" for k, v in (e.get("cambios") if isinstance(e, dict) else e.cambios).items())
    descripcion = e.get("descripcion") if isinstance(e, dict) else e.descripcion
    lectura = e.get("lectura", "") if isinstance(e, dict) else e.lectura
    cadena = e.get("cadena", []) if isinstance(e, dict) else e.cadena
    partes = [f"**{descripcion}**" + (" · escenario propio del studio" if propio else ""), f"Cambios: {cambios or 'ninguno (la base)'}"]
    if lectura:
        partes.append(lectura)
    if cadena:
        partes.append("Mecanismo:\n\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(cadena, 1)))
    return "\n\n".join(partes)
