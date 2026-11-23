"""tests/motor/test_pedagogia.py — la ficha pedagógica de los simuladores (pedagogia.py, base.Pedagogia).

Qué se prueba:
- las fichas reales (los simuladores que enlaza macroeconomia-i) no tienen errores y su clave se comprueba contra el
  modelo; una clave que contradice al modelo es un error, y `base.verificar` la cuenta como una verificación fallida;
- el validador rechaza lo que el estándar de docencia rechaza (nivel SOLO, Bloom, ítem mal formado, control fuera de
  rango, resultado inexistente) y su regla del ítem coincide con la de `docencia/scripts/alineamiento.py` cuando ese
  repo está (se localiza por `core/env.py`, como hace el motor con datafw);
- los ítems que exporta pasan por `alineamiento.quiz_aula` (lo que lee el aula) una vez verificados, y no antes;
- catalogo.json y navegador.json solo llevan la ficha pedagógica verificada y sin las claves del docente.
"""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

# El main.py de la raíz (el laboratorio entero: _cargar aísla cada disciplina), con nombre propio: el studio tiene
# otro `main` y las pruebas de tests/studio lo importan en la misma sesión.
_spec = importlib.util.spec_from_file_location("simuladores_main", RAIZ / "main.py")
main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(main)

REFS = ("macro/m04", "macro/m10", "macro/m20")          # los que enlaza docencia/…/macroeconomia-i/curso.yml


def _con_modelos(refs, hacer):
    """hacer(modelo, base, pedagogia) dentro del espacio de nombres de la disciplina de cada ref."""
    salida = {}
    por_disc = {}
    for r in refs:
        por_disc.setdefault(r.split("/")[0], []).append(r.split("/")[1])
    for disc in main.disciplinas():
        if disc.name not in por_disc:
            continue

        def dentro(config, lista, disc=disc):
            import base
            import pedagogia
            for m, _ in lista:
                if m.id in por_disc[disc.name]:
                    salida[f"{disc.name}/{m.id}"] = hacer(m, base, pedagogia)
        main._cargar(disc, dentro)
    return salida


def _alineamiento():
    """docencia/scripts/alineamiento.py, si el repo hermano está (por core/env.py); si no, None."""
    d = RAIZ
    while d != d.parent and not (d / "core" / "env.py").is_file():
        d = d.parent
    if not (d / "core" / "env.py").is_file():
        return None
    spec = importlib.util.spec_from_file_location("_env_prueba", d / "core" / "env.py")
    env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(env)
    ruta = Path(env.CLASS_DIR) / "scripts" / "alineamiento.py"
    if not ruta.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_alineamiento_prueba", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_las_fichas_reales_no_tienen_errores_y_cumplen_el_minimo():
    def revisar(m, base, pedagogia):
        err, av = pedagogia.problemas(m)
        ped = m.ficha.pedagogia
        return err, av, ped, [n for n, ok, _ in base.verificar(m) if not ok], pedagogia.items(m)
    datos = _con_modelos(REFS, revisar)
    assert set(datos) == set(REFS)
    for ref, (err, av, ped, fallidas, items) in datos.items():
        assert err == [], f"{ref}: {err}"
        assert fallidas == [], f"{ref}: verificaciones fallidas {fallidas}"
        assert len(ped.resultados) >= 1 and len(ped.ejercicios) >= 3
        assert all(e.espera or e.valores for e in ped.ejercicios)
        assert any("sin verificar" in x for x in av)            # lo propuso la IA: verificacion pendiente (C3.3)
        assert len(items) == 2 * len(ped.ejercicios)            # la predicción cerrada y la explicación abierta
        assert len({i["id"] for i in items}) == len(items) and all(i["id"].startswith(ref.split("/")[1]) for i in items)


def test_una_clave_que_contradice_al_modelo_es_un_error_y_una_verificacion_fallida():
    def romper(m, base, pedagogia):
        m2 = copy.deepcopy(m)
        ej = m2.ficha.pedagogia.ejercicios[0]
        ej.espera = {k: ("↓" if v == "↑" else "↑") for k, v in ej.espera.items()}
        ej.valores = {k: v * 2 + 1 for k, v in ej.valores.items()}
        err, _ = pedagogia.problemas(m2)
        fila = [x for x in base.verificar(m2) if x[0].startswith("ficha pedagógica")]
        return err, fila
    for ref, (err, fila) in _con_modelos(["macro/m10"], romper).items():
        assert any("se espera ↓ en «Y* (producto)»" in e for e in err), err
        assert any("se espera «Y* (producto)» =" in e for e in err), err
        assert fila and fila[0][1] is False


def test_el_validador_rechaza_lo_que_docencia_rechaza():
    def romper(m, base, pedagogia):
        casos = {}
        def caso(nombre, cambiar):
            m2 = copy.deepcopy(m)
            cambiar(m2.ficha.pedagogia)
            casos[nombre] = pedagogia.problemas(m2)[0]
        caso("solo", lambda p: setattr(p.resultados[0], "nivel", "alto"))
        caso("bloom", lambda p: setattr(p.ejercicios[0], "bloom", "memorizar"))
        caso("resultado", lambda p: setattr(p.ejercicios[0], "resultado", "r9"))
        caso("escenario", lambda p: setattr(p.ejercicios[0], "escenario", "no_existe"))
        caso("rango", lambda p: (setattr(p.ejercicios[2], "cambios", {"h": 500.0})))
        caso("parametro", lambda p: (setattr(p.ejercicios[2], "cambios", {"zeta": 1.0})))
        caso("ambos", lambda p: setattr(p.ejercicios[2], "escenario", "expansion_fiscal"))
        caso("respuesta", lambda p: p.ejercicios[0].item.__setitem__("respuesta", "otra"))
        caso("distractor", lambda p: p.ejercicios[0].item["errores"].append(
            {"opcion": p.ejercicios[0].item["respuesta"], "error": "x"}))
        caso("id", lambda p: p.ejercicios[0].item.__setitem__("id", "x"))
        caso("explicar", lambda p: setattr(p.ejercicios[1], "explicar", ""))
        caso("origen", lambda p: setattr(p, "origen", {"autor": "llm", "verificacion": "pendiente"}))
        return casos
    casos = _con_modelos(["macro/m10"], romper)["macro/m10"]
    esperado = {"solo": "taxonomía SOLO", "bloom": "bloom «memorizar»", "resultado": "«r9» no está",
                "escenario": "no existe", "rango": "fuera del rango", "parametro": "«zeta» no existe",
                "ambos": "uno de los dos", "respuesta": "no está entre las opciones",
                "distractor": "la opción correcta no es un distractor", "id": "no lleva id",
                "explicar": "falta `explicar`", "origen": "con qué herramienta"}
    for nombre, texto in esperado.items():
        assert any(texto in e for e in casos[nombre]), (nombre, casos[nombre])


def test_la_regla_del_item_es_la_de_docencia():
    alin = _alineamiento()
    if alin is None:
        pytest.skip("docencia no está junto a simuladores")
    import pedagogia as ped_mod
    assert ped_mod.NIVELES_SOLO == alin.NIVELES_SOLO and ped_mod.NIVELES_BLOOM == alin.NIVELES_BLOOM
    assert ped_mod.TIPOS_ITEM == alin.TIPOS_PREGUNTA and ped_mod.DIFICULTADES == alin.DIFICULTADES
    items = sum(_con_modelos(REFS, lambda m, base, pedagogia: pedagogia.items(m)).values(), [])
    for it in items:
        err, _ = alin.problemas_item(it, None)
        assert err == [], (it["id"], err)
    malos = [{"tipo": "opcion", "enunciado": "x", "respuesta": "c", "opciones": ["a", "b"]},
             {"tipo": "vf", "enunciado": "x", "respuesta": "sí"},
             {"tipo": "numerica", "enunciado": "x", "respuesta": "1", "tolerancia": 0.1},
             {"tipo": "abierta", "enunciado": "x", "respuesta": "y", "bloom": "saber"}]
    for p in malos:
        assert bool(ped_mod.problemas_item(p)) == bool(alin.problemas_item(p, None)[0]), p


def test_el_aula_lee_los_items_verificados_y_no_los_pendientes():
    alin = _alineamiento()
    if alin is None:
        pytest.skip("docencia no está junto a simuladores")
    items = sum(_con_modelos(REFS, lambda m, base, pedagogia: pedagogia.items(m)).values(), [])
    assert not any(alin.publicable(i) for i in items)          # pendientes: el aula no los recibe
    verificados = [dict(i, origen=dict(i["origen"], verificacion="verificada")) for i in items]
    quiz = alin.quiz_aula([("s00", i) for i in verificados])
    cerradas = [i for i in items if i["tipo"] != "abierta"]
    assert len(quiz) == len(cerradas) == 9                      # las abiertas no se corrigen solas
    opcion = next(q for q in quiz if q["id"] == "m10-e1-predecir")
    assert opcion["opciones"][opcion["correcta"]] == "Baja, porque sube la tasa de interés"
    assert opcion["retro"][opcion["correcta"]] is None and all(opcion["retro"][i] for i in (0, 2))
    numerica = next(q for q in quiz if q["id"] == "m04-e2-predecir")
    assert numerica["respuesta"] == 2.78 and numerica["tolerancia"] == 0.01


def test_los_contratos_solo_llevan_lo_verificado_y_sin_claves():
    def contrato(m, base, pedagogia):
        antes = pedagogia.para_contrato(m)
        m2 = copy.deepcopy(m)
        m2.ficha.pedagogia.origen = dict(m2.ficha.pedagogia.origen, verificacion="verificada")
        return antes, pedagogia.para_contrato(m2), main._ficha(m, ""), main._ficha_web(m, "")
    for ref, (antes, despues, cat, web) in _con_modelos(REFS, contrato).items():
        assert antes is None and "pedagogia" not in cat and "pedagogia" not in web
        assert [r["id"] for r in despues["resultados"]] == ["r1", "r2"] and len(despues["ejercicios"]) == 3
        texto = repr(despues)
        for ej in despues["ejercicios"]:
            assert ej["predecir"] and ej["mover"] and ej["explicar"] and ej["comparar"]
            assert {"respuesta", "valor", "errores", "origen"}.isdisjoint(ej.get("item", {}))
        assert "Respuesta esperada" not in texto and "error_comun" not in texto


def test_hojas_y_banco():
    def vistas(m, base, pedagogia):
        return pedagogia.markdown(m), pedagogia.markdown(m, docente=True), pedagogia.banco(m)
    alumno, docente, banco = _con_modelos(["macro/m04"], vistas)["macro/m04"]
    assert alumno.startswith("# m04 · Multiplicador keynesiano: hoja del alumno")
    assert "**Predice** (antes de mover nada)" in alumno and "Respuesta esperada" not in alumno
    assert "Propensión marginal a consumir c: de 0,8 a 0,9" in alumno
    assert "Clave de la predicción: Se duplica, de 500 a 1 000" in docente and "Pendiente para el autor" in docente
    import yaml
    items = yaml.safe_load(banco)
    assert [i["id"] for i in items][:2] == ["m04-e1-predecir", "m04-e1-explicar"]
    assert items[1]["tipo"] == "abierta" and items[1]["errores"][0]["error"]


def test_un_modelo_sin_ficha_pedagogica_no_cambia():
    def sin(m, base, pedagogia):
        return pedagogia.problemas(m), pedagogia.items(m), pedagogia.markdown(m), [n for n, *_ in base.verificar(m)]
    (prob, items, md, nombres), = _con_modelos(["macro/m01"], sin).values()
    assert prob == ([], []) and items == [] and md == ""
    assert not any(n.startswith("ficha pedagógica") for n in nombres)


def test_la_orden_de_la_cli(capsys):
    import argparse
    assert main.cmd_pedagogia(argparse.Namespace(ref=None, formato="resumen", verificar=True)) == 0
    salida = capsys.readouterr().out
    assert all(r in salida for r in REFS) and "0 errores" in salida
    assert main.cmd_pedagogia(argparse.Namespace(ref="macro/m01", formato="alumno", verificar=False)) == 1
    assert main.cmd_pedagogia(argparse.Namespace(ref="macro/m10", formato="banco", verificar=False)) == 0
    assert "m10-e3-explicar" in capsys.readouterr().out


def test_el_fundamento_se_comprueba_contra_calibre():
    """Las citas del diseño (pedagogia.FUNDAMENTO) están en la hoja que dicen; sin biblioteca, la prueba se salta."""
    def comprobar(m, base, pedagogia):
        import fuentes
        return [(f.calibre_id, f.pagina, *fuentes.comprobar(f)) for f in pedagogia.FUNDAMENTO]
    filas = _con_modelos(["macro/m04"], comprobar)["macro/m04"]
    if all(estado == "no comprobable" for *_, estado, _ in filas):
        pytest.skip("la biblioteca Calibre no está en esta máquina")
    for cid, pagina, estado, detalle in filas:
        assert estado in ("verificada", "aviso"), (cid, pagina, detalle)   # aviso: la página web no tiene folio
    assert {cid for cid, *_ in filas} == {11175, 11161, 10516}
