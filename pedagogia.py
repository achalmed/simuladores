"""simuladores/pedagogia.py — la ficha pedagógica de un simulador: validarla, comprobarla contra el modelo y exportarla.

Objetivo: que cada simulador que usa un curso diga qué aprende el alumno con él (resultados con su nivel SOLO), qué
  pregunta ayuda a responder, con qué supuestos, y cómo se practica: ejercicios en el ciclo predecir, observar,
  explicar y comparar con lo predicho, con la respuesta esperada y el error común que anticipan.
Método: los datos viven en el modelo (`base.Pedagogia` en `Ficha.pedagogia`); aquí se validan con el vocabulario de
  docencia (estándar §10.1 y §10.2), y la respuesta esperada de cada ejercicio, dicha como aserción (`espera`,
  `valores`), se comprueba corriendo el modelo: la clave del docente no puede contradecir al simulador. `base.verificar`
  lo llama como una verificación más. Los ejercicios salen como ítems del banco de docencia (`banco`), como hoja del
  alumno sin claves o con ellas (`markdown`) y, solo si están verificados, en catalogo.json y navegador.json.
Fundamento: docs/pedagogia.md (Freeman et al., 2014; Chi y Wylie, 2014; y las obras pendientes de ingresar).
Límite: el vocabulario se copia de `docencia/scripts/alineamiento.py` porque el motor no lee otros repos; la prueba
  `tests/motor/test_pedagogia.py` lo compara con el de docencia cuando está, para que no diverjan.
Uso: `python3 main.py pedagogia [REF] [--formato resumen|alumno|docente|banco] [--verificar]`.
"""
from __future__ import annotations

import base

# El vocabulario de docencia (docencia/scripts/alineamiento.py, estándar §10.1 y §10.2).
NIVELES_SOLO = ("uniestructural", "multiestructural", "relacional", "abstracto_ampliado")
NIVELES_BLOOM = ("recordar", "comprender", "aplicar", "analizar", "evaluar", "crear")
TIPOS_ITEM = ("abierta", "opcion", "vf", "numerica")
DIFICULTADES = ("baja", "media", "discriminante")
AUTORES = ("persona", "llm")
VERIFICACIONES = ("pendiente", "verificada")
SIGNOS = ("↑", "↓", "=")
TOLERANCIA_RELATIVA = 0.005          # una cifra esperada redondeada a tres o cuatro dígitos cabe en 0,5 %
# Las obras que fundan el diseño, como citas comprobables (`fuentes.comprobar`, la misma regla que Ficha.fuentes); las que
# no están en Calibre se listan en docs/pedagogia.md §5 como pendientes, con su referencia completa.
FUNDAMENTO = (
    base.Fuente(11175, "8413", 4, "Active learning engages students in the process of learning through",
                "el simulador se usa con una tarea del alumno, no como demostración que se mira"),
    base.Fuente(11175, "8410", 1, "students in classes with traditional lecturing were 1.5 times more",
                "por qué el ejercicio sustituye a la exposición del modelo, no la adorna"),
    base.Fuente(11175, "8411", 2, "diagnose known misconceptions, in contrast to course examinations",
                "cada ejercicio declara el error común que anticipa, y cada distractor el suyo"),
    base.Fuente(11161, "222", 5, "generate or produce additional externalized outputs or",
                "predecir y explicar por escrito es el modo constructivo de ICAP"),
    base.Fuente(11161, "222", 5, "generating predictions (Schauble, Glaser, Duschl,",
                "la predicción antes de mover el control es una actividad constructiva"),
    base.Fuente(11161, "224", 7, "selecting is only active in our taxonomy",
                "elegir una opción o mover un deslizador solo es activo: por eso cada ejercicio pide explicar"),
    base.Fuente(11161, "235", 18, "(passive) to an intervention consisting of predicting",
                "predecir y discutir en parejas (la puesta en común) es el modo interactivo"),
    base.Fuente(10516, "s. p.", 1, "The updated version by Anderson and Krathwohl (2001)",
                "el nivel de Bloom del ítem, con la taxonomía revisada que usa docencia"),
)
COMPARAR = ("Lo que observaste, ¿coincide con lo que predijiste? Si no, ¿qué paso de tu razonamiento falló: un "
            "supuesto del modelo, la dirección de un efecto o su tamaño?")


def _ped(modelo):
    f = getattr(modelo, "ficha", None)
    return getattr(f, "pedagogia", None) if f is not None else None


def publicable(ped) -> bool:
    """Lo que propuso una IA no sale al alumno hasta que el docente lo verifica (C3.3; docencia hace lo mismo)."""
    org = getattr(ped, "origen", None)
    return not (isinstance(org, dict) and org.get("autor") == "llm" and org.get("verificacion") != "verificada")


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _cifra(v) -> str:
    """Una cifra de control en español: 0,8; 250; 0,05."""
    return f"{v:g}".replace(".", ",") if _num(v) else str(v)


def cambios(modelo, ej) -> dict:
    """Los valores que el alumno fija: los del escenario o los `cambios` del ejercicio."""
    if ej.escenario:
        return dict(modelo.escenario(ej.escenario).cambios)
    return dict(ej.cambios)


def consigna_mover(modelo, ej) -> str:
    """Qué control mover y hasta dónde, dicho con la etiqueta de cada parámetro."""
    try:
        c = cambios(modelo, ej)
    except KeyError:
        return ""
    partes = []
    for nombre, valor in c.items():
        try:
            p = modelo.parametro(nombre)
        except KeyError:
            partes.append(f"{nombre} = {_cifra(valor)}")
            continue
        partes.append(f"{p.etiqueta or p.nombre}: de {_cifra(p.valor)} a {_cifra(valor)}")
    texto = "; ".join(partes)
    if ej.escenario:
        texto = f"el escenario «{modelo.escenario(ej.escenario).descripcion}» ({texto})"
    return texto


# ── el ítem del banco de docencia ────────────────────────────────────────────────────────────────────────────────

def problemas_item(p: dict) -> list[str]:
    """Errores de un ítem en el esquema de docencia §10.2 (la misma regla que `alineamiento.problemas_item`)."""
    err = []
    tipo, resp = p.get("tipo"), p.get("respuesta")
    ops = [str(o) for o in p.get("opciones") or []]
    if tipo not in TIPOS_ITEM:
        err.append(f"tipo «{tipo}» fuera de {list(TIPOS_ITEM)}")
    if not str(p.get("enunciado") or "").strip() or resp in (None, ""):
        err.append("sin enunciado o sin respuesta")
    if tipo == "opcion":
        if len(ops) < 2:
            err.append("una pregunta de opción necesita al menos dos opciones")
        if len(set(ops)) != len(ops):
            err.append("opciones repetidas")
        if resp not in (None, "") and str(resp) not in ops:
            err.append("la respuesta no está entre las opciones")
    elif ops:
        err.append("`opciones` solo van en una pregunta de opción")
    if tipo == "vf" and resp not in (None, "") and not isinstance(resp, bool):
        err.append("la respuesta de verdadero o falso es true o false")
    if "valor" in p and (tipo != "numerica" or not _num(p["valor"])):
        err.append("`valor` es el número de una pregunta numérica")
    if "tolerancia" in p and ("valor" not in p or not _num(p["tolerancia"]) or p["tolerancia"] < 0):
        err.append("`tolerancia` es un número no negativo y va con `valor`")
    if "unidad" in p and "valor" not in p:
        err.append("`unidad` va con `valor`")
    lista = p.get("errores")
    if lista is not None:
        if not isinstance(lista, list):
            err.append("`errores` es una lista de {opcion?, error}")
            lista = []
        for e in lista:
            if not isinstance(e, dict) or not str(e.get("error") or "").strip():
                err.append("cada error común lleva su `error`")
            elif "opcion" in e:
                o = str(e["opcion"])
                if tipo != "opcion":
                    err.append("`errores[].opcion` solo va en una pregunta de opción")
                elif o not in ops:
                    err.append(f"error común de una opción que no está: «{o}»")
                elif o == str(resp):
                    err.append("la opción correcta no es un distractor")
    if "bloom" in p and p["bloom"] not in NIVELES_BLOOM:
        err.append(f"bloom «{p['bloom']}» fuera de {list(NIVELES_BLOOM)}")
    if "dificultad" in p and p["dificultad"] not in DIFICULTADES:
        err.append(f"dificultad «{p['dificultad']}» fuera de {list(DIFICULTADES)}")
    return err


def item_predecir(modelo, ej, ped=None) -> dict | None:
    """La predicción como ítem cerrado del banco (id y resultado del ejercicio; origen de la ficha)."""
    if not isinstance(ej.item, dict):
        return None
    ped = ped or _ped(modelo)
    it = {"id": f"{modelo.id}-{ej.id}-predecir", "resultado": ej.resultado} | dict(ej.item)
    if ped is not None and isinstance(ped.origen, dict) and "origen" not in it:
        it["origen"] = dict(ped.origen)
    return it


def item_explicar(modelo, ej, ped=None) -> dict:
    """La explicación como pregunta abierta del banco: mover, observar, explicar y comparar; la respuesta esperada y
    el error común, para la puesta en común."""
    ped = ped or _ped(modelo)
    mover = consigna_mover(modelo, ej)
    pasos = [f"Simulador «{modelo.id} · {modelo.nombre}». Antes de mover nada: {ej.predecir}",
             f"Mueve {mover}." if mover else "", f"Observa {ej.observar}" if ej.observar else "", ej.explicar,
             ej.comparar or COMPARAR]
    it = {"id": f"{modelo.id}-{ej.id}-explicar", "resultado": ej.resultado, "tipo": "abierta",
          "enunciado": " ".join(p for p in pasos if p), "respuesta": ej.respuesta,
          "errores": [{"error": ej.error_comun}]}
    if ej.bloom:
        it["bloom"] = ej.bloom
    if ped is not None and isinstance(ped.origen, dict):
        it["origen"] = dict(ped.origen)
    return it


def items(modelo) -> list[dict]:
    """Los ítems del banco de docencia que da el simulador: por ejercicio, la predicción (si es cerrada) y la
    explicación."""
    ped = _ped(modelo)
    if ped is None:
        return []
    out = []
    for ej in ped.ejercicios:
        p = item_predecir(modelo, ej, ped)
        if p is not None:
            out.append(p)
        out.append(item_explicar(modelo, ej, ped))
    return out


# ── validar y comprobar ──────────────────────────────────────────────────────────────────────────────────────────

def comprobar(modelo, ej) -> list[str]:
    """La respuesta esperada (`espera`, `valores`) frente a lo que el modelo calcula al mover lo que dice el ejercicio."""
    err = []
    try:
        c = cambios(modelo, ej)
        res_base, res = modelo.calcular(), modelo.calcular(**c)
    except KeyError as exc:
        return [f"{ej.id}: {exc}"]
    except Exception as exc:                 # noqa: BLE001 — un cálculo que revienta es un fallo del ejercicio
        return [f"{ej.id}: el modelo no calcula con esos cambios ({exc})"]
    for mag, s in ej.espera.items():
        if s not in SIGNOS:
            err.append(f"{ej.id}: «{s}» no es ↑, ↓ ni =")
        elif mag not in res:
            err.append(f"{ej.id}: «{mag}» no está en los resultados del modelo")
        elif base.signo(res[mag] - res_base[mag]) != s:
            err.append(f"{ej.id}: se espera {s} en «{mag}», y el modelo da {base.fmt(res_base[mag])} → "
                       f"{base.fmt(res[mag])}")
    for mag, v in ej.valores.items():
        if mag not in res:
            err.append(f"{ej.id}: «{mag}» no está en los resultados del modelo")
        elif not _num(v) or abs(res[mag] - v) > max(TOLERANCIA_RELATIVA * abs(v), 1e-9):
            err.append(f"{ej.id}: se espera «{mag}» = {v}, y el modelo da {base.fmt(res[mag])}")
    return err


def problemas(modelo) -> tuple[list[str], list[str]]:
    """(errores, avisos) de la ficha pedagógica del modelo. Sin ficha pedagógica, nada."""
    ped = _ped(modelo)
    if ped is None:
        return [], []
    err, av = [], []
    f = modelo.ficha
    if not str(f.pregunta or "").strip():
        err.append("la ficha pedagógica pide la pregunta que el simulador ayuda a responder (`Ficha.pregunta`)")
    if not f.supuestos:
        err.append("la ficha pedagógica pide los supuestos del modelo (`Ficha.supuestos`)")
    ids_r = [r.id for r in ped.resultados]
    if not ped.resultados:
        err.append("sin resultados de aprendizaje")
    if len(set(ids_r)) != len(ids_r):
        err.append("resultados con id repetido")
    for r in ped.resultados:
        if r.nivel not in NIVELES_SOLO:
            err.append(f"resultado {r.id}: nivel «{r.nivel}» fuera de la taxonomía SOLO {list(NIVELES_SOLO)}")
        if not str(r.enunciado or "").strip():
            err.append(f"resultado {r.id}: sin enunciado")
    ids_e = [e.id for e in ped.ejercicios]
    if not ped.ejercicios:
        err.append("sin ejercicios para el alumno")
    if len(set(ids_e)) != len(ids_e):
        err.append("ejercicios con id repetido")
    usados = set()
    for ej in ped.ejercicios:
        usados.add(ej.resultado)
        if ej.resultado not in ids_r:
            err.append(f"{ej.id}: el resultado «{ej.resultado}» no está en la ficha")
        for campo in ("predecir", "explicar", "respuesta", "error_comun"):
            if not str(getattr(ej, campo) or "").strip():
                err.append(f"{ej.id}: falta `{campo}` (el ciclo es predecir, mover, explicar y comparar)")
        if bool(ej.escenario) == bool(ej.cambios):
            err.append(f"{ej.id}: se mueve un escenario o unos `cambios`, uno de los dos")
        elif ej.escenario and ej.escenario not in {e.nombre for e in modelo.escenarios}:
            err.append(f"{ej.id}: el escenario «{ej.escenario}» no existe en el modelo")
        else:
            nombres = {p.nombre for p in modelo.parametros}
            for nombre, valor in cambios(modelo, ej).items():
                if nombre not in nombres:
                    err.append(f"{ej.id}: el parámetro «{nombre}» no existe en el modelo")
                    continue
                p = modelo.parametro(nombre)
                if not _num(valor) or not (p.minimo <= valor <= p.maximo):
                    err.append(f"{ej.id}: {nombre} = {valor} queda fuera del rango del control "
                               f"[{p.minimo:g}, {p.maximo:g}]: el alumno no lo podría mover ahí")
        if not ej.espera and not ej.valores:
            err.append(f"{ej.id}: sin `espera` ni `valores`, la respuesta esperada no se comprueba contra el modelo")
        if ej.bloom and ej.bloom not in NIVELES_BLOOM:
            err.append(f"{ej.id}: bloom «{ej.bloom}» fuera de {list(NIVELES_BLOOM)}")
        if ej.item is not None:
            if not isinstance(ej.item, dict):
                err.append(f"{ej.id}: `item` es un dict en el esquema del banco de docencia")
            else:
                if "id" in ej.item or "resultado" in ej.item:
                    err.append(f"{ej.id}: el `item` no lleva id ni resultado: los toma del ejercicio")
                if ej.item.get("tipo") == "abierta":
                    err.append(f"{ej.id}: la predicción abierta va en `predecir`; `item` es para una cerrada")
                err += [f"{ej.id} (ítem): {e}" for e in problemas_item(ej.item)]
                if (ej.item.get("tipo") == "numerica" and _num(ej.item.get("valor")) and ej.valores
                        and not any(_num(v) and abs(v - ej.item["valor"]) <= max(TOLERANCIA_RELATIVA * abs(v), 1e-9)
                                    for v in ej.valores.values())):
                    av.append(f"{ej.id}: el `valor` del ítem no coincide con ninguna cifra de `valores`")
        err += comprobar(modelo, ej)
    for r in ped.resultados:
        if r.id not in usados:
            av.append(f"resultado {r.id}: ningún ejercicio lo practica")
    org = ped.origen
    if org is not None:
        if not isinstance(org, dict) or org.get("autor") not in AUTORES:
            err.append(f"`origen.autor` es {' o '.join(AUTORES)}")
        elif org["autor"] == "llm":
            if not org.get("herramienta"):
                err.append("lo que propuso una IA dice con qué herramienta (`origen.herramienta`)")
            if org.get("verificacion", "pendiente") not in VERIFICACIONES:
                err.append(f"`origen.verificacion` es {' o '.join(VERIFICACIONES)}")
    if not publicable(ped):
        av.append("propuesta por la IA y sin verificar: no sale al alumno hasta `verificacion: verificada`")
    for p in ped.pendientes:
        av.append(f"pendiente para el autor: {p}")
    return err, av


def resumen(modelo) -> str:
    ped = _ped(modelo)
    if ped is None:
        return "sin ficha pedagógica"
    cerrados = sum(1 for e in ped.ejercicios if isinstance(e.item, dict))
    estado = "verificada" if publicable(ped) else "por verificar"
    return (f"{len(ped.resultados)} resultados, {len(ped.ejercicios)} ejercicios ({cerrados} con predicción cerrada), "
            f"respuestas comprobadas contra el modelo; {estado}")


# ── las vistas: la hoja del alumno o del docente, el banco y los contratos JSON ──────────────────────────────────

def _respuesta(it: dict) -> str:
    r = it.get("respuesta")
    return ("Verdadero" if r else "Falso") if isinstance(r, bool) else str(r)


def markdown(modelo, docente: bool = False, completo: bool = True) -> str:
    """La hoja de trabajo del simulador: pregunta, supuestos, resultados y ejercicios. Con `docente`, la respuesta
    esperada, el error común, la clave de la predicción cerrada y lo que el autor tiene pendiente. Sin `completo`, solo
    los resultados y los ejercicios (la ficha del studio ya trae la pregunta y los supuestos)."""
    ped = _ped(modelo)
    if ped is None:
        return ""
    h = "#"
    f = modelo.ficha
    partes = []
    if completo:
        partes.append(f"# {modelo.id} · {modelo.nombre}: " + ("guía del docente" if docente else "hoja del alumno"))
        if f.pregunta:
            partes.append(f"> {f.pregunta}")
        if f.supuestos:
            partes.append(f"{h}# Supuestos del modelo\n\n" + "\n".join(f"- {s}" for s in f.supuestos))
    if docente and not publicable(ped):
        partes.append("*Propuesta por la IA y sin verificar (`origen.verificacion: pendiente`): no se entrega al "
                      "alumno hasta que el docente la verifique.*")
    partes.append(f"{h}# Resultados de aprendizaje\n\n" + "\n".join(
        f"- **{r.id}** ({r.nivel.replace('_', ' ')}): {r.enunciado}" for r in ped.resultados))
    ejercicios = []
    for ej in ped.ejercicios:
        b = [f"{h}## {ej.id} · practica {ej.resultado}" + (f" · {ej.bloom}" if ej.bloom else "")]
        b.append(f"1. **Predice** (antes de mover nada): {ej.predecir}")
        if isinstance(ej.item, dict):
            sufijo = {"vf": " (verdadero o falso)", "numerica": " (una cifra)"}.get(ej.item.get("tipo"), "")
            b.append(f"   {ej.item['enunciado']}{sufijo}")
            if ej.item.get("tipo") == "opcion":
                b.append("\n".join(f"   - {o}" for o in ej.item.get("opciones", [])))
        b.append(f"2. **Mueve** {consigna_mover(modelo, ej)}.")
        if ej.observar:
            b.append(f"3. **Observa** {ej.observar}")
        b.append(f"{4 if ej.observar else 3}. **Explica**: {ej.explicar}")
        b.append(f"{5 if ej.observar else 4}. **Compara**: {ej.comparar or COMPARAR}")
        if docente:
            d = []
            if isinstance(ej.item, dict):
                d.append(f"- Clave de la predicción: {_respuesta(ej.item)}"
                         + (f" (tolerancia {ej.item['tolerancia']:g})" if "tolerancia" in ej.item else ""))
                for e in ej.item.get("errores") or []:
                    d.append(f"  - «{e['opcion']}»: {e['error']}" if "opcion" in e else f"  - {e['error']}")
            d.append(f"- Respuesta esperada: {ej.respuesta}")
            d.append(f"- Error común que anticipa: {ej.error_comun}")
            comprobado = [f"{m} {s}" for m, s in ej.espera.items()] + [f"{m} = {v:g}" for m, v in ej.valores.items()]
            d.append(f"- Comprobado contra el modelo: {', '.join(comprobado)}")
            b.append("\n".join(d))
        ejercicios.append("\n\n".join(b))
    partes.append(f"{h}# Ejercicios: predecir, observar, explicar\n\n" + "\n\n".join(ejercicios))
    if docente and ped.pendientes:
        partes.append(f"{h}# Pendiente para el autor\n\n" + "\n".join(f"- {p}" for p in ped.pendientes))
    return "\n\n".join(partes) + "\n"


def para_contrato(modelo) -> dict | None:
    """La ficha pedagógica en catalogo.json y navegador.json: solo si está verificada, y sin las claves del docente
    (como la vitrina del aula deja fuera `respuesta` y `explicacion` del banco)."""
    ped = _ped(modelo)
    if ped is None or not publicable(ped):
        return None
    ejercicios = []
    for ej in ped.ejercicios:
        e = {"id": ej.id, "resultado": ej.resultado, "predecir": ej.predecir, "cambios": cambios(modelo, ej),
             "escenario": ej.escenario, "mover": consigna_mover(modelo, ej), "observar": ej.observar,
             "explicar": ej.explicar, "comparar": ej.comparar or COMPARAR, "bloom": ej.bloom}
        if isinstance(ej.item, dict):
            e["item"] = {k: v for k, v in item_predecir(modelo, ej, ped).items()
                         if k not in ("respuesta", "valor", "tolerancia", "errores", "explicacion", "origen")}
        ejercicios.append(e)
    return {"resultados": [{"id": r.id, "nivel": r.nivel, "enunciado": r.enunciado} for r in ped.resultados],
            "ejercicios": ejercicios}


def banco(modelo) -> str:
    """Los ítems en YAML, listos para pegar en la lista `preguntas:` de un `recuperacion.yml` de docencia."""
    import yaml
    cabecera = [f"# Ítems del simulador {modelo.id} «{modelo.nombre}» en el esquema del banco de docencia (§10.2).",
                "# GENERADO por simuladores/main.py pedagogia --formato banco; se pega en `preguntas:` del recuperacion.yml.",
                "# `resultado` es el id del simulador: cámbialo por el raN del curso. Lo que propuso la IA sin verificar",
                "# no sale en ninguna exportación de docencia hasta `origen.verificacion: verificada`."]
    ped = _ped(modelo)
    if ped is not None:
        cabecera += [f"#   {r.id} ({r.nivel}): {r.enunciado}" for r in ped.resultados]
    cuerpo = yaml.safe_dump(items(modelo), allow_unicode=True, sort_keys=False, width=110)
    return "\n".join(cabecera) + "\n" + cuerpo
