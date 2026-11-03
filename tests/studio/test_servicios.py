"""tests/studio/test_servicios.py — los servicios de Simuladores Studio sin Qt, sobre el laboratorio de muestra: las
rutas, el laboratorio (las disciplinas aisladas, el catálogo, un modelo importado con un matplotlib vacío), las
corridas (una corrida real del motor, lo que dibuja el gráfico científico, la comparación, el CSV), las
verificaciones y sus estados (la huella del archivo, la salida de la CLI), la ficha en Markdown y el catálogo de
operaciones (las órdenes de la CLI, relativas a la raíz)."""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import HAY_MATPLOTLIB, REPO, muestra_sesion  # noqa: F401

from sim_app.servicios import corridas, fichas, formulas, operaciones as ops, rutas, verificaciones as ver
from sim_app.servicios import laboratorio as lab
from gui_comun import paleta  # noqa: E402  (la de gui-comun 3.1)
from sim_app.servicios import simulacion as sim


@pytest.fixture
def laboratorio(muestra_sesion):
    return lab.Laboratorio(muestra_sesion.raiz)


def test_rutas(muestra_sesion):
    assert rutas.raiz() == muestra_sesion.raiz
    assert rutas.REPO == REPO
    assert "sudo" not in rutas.orden_crear_venv() and "apt" not in rutas.orden_crear_venv()
    assert rutas.relativa(muestra_sesion.raiz / "demo" / "main.py") == "demo/main.py"
    assert rutas.interprete().endswith("python") or rutas.interprete().endswith("python3")


def test_matplotlib_vacio_no_cuenta_ni_rompe(monkeypatch):
    """Con el matplotlib vacío de navegador.py en sys.modules (un intérprete sin matplotlib), `find_spec` lanzaría
    ValueError: la ficha y la figura dicen «sin matplotlib» en vez de romper al abrir un modelo (2026-11-03)."""
    import sys
    import types
    vacio = types.ModuleType("matplotlib")
    monkeypatch.setitem(sys.modules, "matplotlib", vacio)
    assert rutas.hay_matplotlib() is False and formulas.disponible() is False


def test_catalogo_y_disciplinas(muestra_sesion):
    c = lab.catalogo(muestra_sesion.raiz)
    assert c["disciplinas"] == ["demo"] and c["total"] == 3
    assert [m["ref"] for m in c["modelos"]] == ["demo/d01", "demo/d02", "demo/d03"]
    assert lab.disciplinas(muestra_sesion.raiz) == ["demo"]
    assert lab.nombre_de("demo") == "Demostración" and lab.nombre_de("otra") == "Otra"


def test_laboratorio_importa_el_modelo_sin_matplotlib_real(laboratorio):
    m = laboratorio.modelo("demo", "d01")
    assert m.id == "d01" and len(m.parametros) == 4 and len(m.escenarios) == 2
    assert laboratorio.archivo("demo", "d01").name == "d01_mercado_lineal.py"
    assert laboratorio.config().AREA == "demo"
    assert laboratorio.base().verificar(m)[0][1] is True
    assert laboratorio.navegador().calcular(m, {})["resultados"][0][0] == "Q* (cantidad)"


def test_corrida_real_y_grafico(laboratorio):
    m = laboratorio.modelo("demo", "d01")
    corrida = corridas.correr(laboratorio.navegador(), m, {"a": 130})
    assert corrida["valores"]["a"] == 130 and corrida["curvas"]["equilibrio"]["x"] == pytest.approx(27.5)
    g = sim.grafico(corrida["curvas"], m.xlabel, m.ylabel)
    assert [s["nombre"] for s in g["lineas"]] == ["Demanda D", "Oferta S"] and [s["rol"] for s in g["lineas"]] == ["azul", "rojo"]
    assert g["lineas"][0]["x"] == corrida["curvas"]["lineas"][0]["x"]                         # la x del motor, sin rejilla
    assert g["limites"]["xMin"] == 0 and g["limites"]["xMax"] == 50
    assert g["equilibrio"] == {"x": 27.5, "y": 75.0}
    assert g["etiquetaX"] == "Cantidad (Q)" and g["etiquetaY"] == "Precio (P)" and not g["temporal"]
    assert g["limites"]["yMin"] < 20 and g["limites"]["yMax"] > 130
    base = corridas.correr(laboratorio.navegador(), m, {})
    filas = corridas.comparar(base["resultados"], corrida["resultados"])
    assert filas[0]["magnitud"] == "Q* (cantidad)" and filas[0]["signo"] == "↑" and filas[0]["pct"].startswith("+")
    csv = corridas.csv_series(corrida["curvas"])
    assert csv.splitlines()[0].startswith("x · Demanda") and len(csv.splitlines()) == 102


def test_grafico_de_barras_y_marcas(laboratorio):
    m = laboratorio.modelo("demo", "d02")
    corrida = corridas.correr(laboratorio.navegador(), m, {})
    g = sim.grafico(corrida["curvas"], m.xlabel, m.ylabel)
    assert g["barras"]["categorias"] == ["S", "I", "G"] and g["barras"]["valores"] == [180.0, 100.0, 80.0]
    assert g["barras"]["roles"] == ["rojo", "verde", "verde"]                                   # filtración e inyecciones
    assert g["lineas"] == [] and g["limites"]["yMin"] == 0.0 and g["anotacion"].startswith("Y* = 900")
    vertical = sim.grafico({"lineas": [{"etiqueta": "$Y^*$", "x": [3, 3], "y": [0, 10]}, {"etiqueta": "L", "x": [0, 5], "y": [1, 2]}]})
    assert vertical["verticales"] == [{"x": 3.0, "nombre": "Y*", "rol": "azul"}] and [s["nombre"] for s in vertical["lineas"]] == ["L"]


def test_verificaciones_y_estados(laboratorio, tmp_path):
    m1, m2 = laboratorio.modelo("demo", "d01"), laboratorio.modelo("demo", "d02")
    a1, a2 = laboratorio.archivo("demo", "d01"), laboratorio.archivo("demo", "d02")
    filas1 = ver.verificar(laboratorio.base(), m1, a1, None, "la muestra")
    assert [f["ok"] for f in filas1] == [True, True, True] and filas1[0]["mensaje"].startswith("coherencia")
    assert filas1[1]["fuente"] == "la muestra" and filas1[1]["archivo"] == a1.name
    filas2 = ver.verificar(laboratorio.base(), m2, a2)
    assert [f["ok"] for f in filas2] == [True, True, False] and filas2[2]["nivel"] == "error" and "esperado > 1000" in filas2[2]["detalle"]
    estados = ver.Estados(tmp_path / "verificaciones.json")
    assert estados.estado("demo/d01", a1) == "sin_verificar"
    estados.registrar("demo/d01", a1, *ver.resumen(filas1))
    estados.registrar("demo/d02", a2, *ver.resumen(filas2), fallos=["Y* mayor que 1000"])
    assert estados.estado("demo/d01", a1) == "verificado" and estados.estado("demo/d02", a2) == "diferencias"
    otra = ver.Estados(tmp_path / "verificaciones.json")
    assert otra.registro("demo/d02")["fallos"] == ["Y* mayor que 1000"]
    a1.write_text(a1.read_text(encoding="utf-8") + "\n# tocado\n", encoding="utf-8")
    import os
    os.utime(a1, (a1.stat().st_atime + 5, a1.stat().st_mtime + 5))
    assert otra.estado("demo/d01", a1) == "sin_verificar"                       # el archivo cambió
    salida = "  ✔ d01   demanda = oferta en Q*: ok\n  ✘ d02   Y* mayor que 1000: no\n  ✔ d02   S = I + G: ok\n\n2/3 verificaciones superadas"
    cuenta = otra.desde_salida_cli("demo", salida, {"d01": a1, "d02": a2})
    assert cuenta == {"demo/d01": (1, 1), "demo/d02": (1, 2)} and otra.estado("demo/d01", a1) == "verificado"


def test_ficha_markdown(laboratorio, muestra_sesion):
    m = laboratorio.modelo("demo", "d01")
    fila = lab.catalogo(muestra_sesion.raiz)["modelos"][0]
    md = fichas.markdown(m, fila, "por defecto", {}, fila["archivo"])
    assert md.startswith("# d01 · Mercado lineal") and "## Ecuaciones" in md and "`P = a - b\\,Q`" in md
    assert "**Sección**: I · Mercados (nivel 1)" in md and "## Procedencia\n\npor defecto" in md
    con_imagen = fichas.markdown(m, fila, "", {"P = a - b\\,Q": Path("/x/f.png")})
    assert "![P = a - b ,Q](file:///x/f.png)" in con_imagen                       # sin escapes: Qt no repite la imagen
    lectura = fichas.escenario_markdown({"descripcion": "sube", "cambios": {"a": 130.0}, "lectura": "suben", "cadena": ["↑a", "↑Q*"]})
    assert lectura.startswith("**sube**") and "Cambios: a = 130.0" in lectura and "2. ↑Q*" in lectura
    assert corridas.sin_mathtext("Producto ($Y$)") == "Producto (Y)" and corridas.sin_mathtext(r"$\bar X$ y $\sigma$") == "X y σ"


def test_formulas(tmp_path):
    assert formulas.preparar(r"\text{con media} \tfrac{a}{b}") == r"\mathrm{con\ media} \frac{a}{b}"
    ruta = formulas.imagen("Y = C + I", "#000000", tmp_path / "f")
    if HAY_MATPLOTLIB and formulas.disponible():
        assert ruta is not None and ruta.is_file() and ruta.stat().st_size > 100
        assert formulas.imagen("Y = C + I", "#000000", tmp_path / "f") == ruta
    else:
        assert ruta is None


def test_operaciones(muestra_sesion):
    ids = [o.id for o in ops.OPERACIONES]
    assert ids[:2] == ["correr", "verificar"] and {"reporte", "datos", "guardar_escenario", "verificar_disciplina", "catalogo", "web"} <= set(ids)
    assert all(o.escribe == (o.aplicar is not None or o.en_proceso in ("guardar", "datos")) for o in ops.OPERACIONES)
    ctx = ops.Contexto(raiz=muestra_sesion.raiz, disciplina="demo", id="d01", valor="a", escenarios=["mas_demanda"])
    assert ops.operacion("sensibilidad").simular(ctx).texto() == "cd demo && python3 main.py sensibilidad d01 --param a"
    assert ops.operacion("comparar").simular(ctx).texto() == "cd demo && python3 main.py comparar d01 mas_demanda"
    assert ops.operacion("catalogo").simular(ctx).texto() == "python3 main.py catalogo --verificar"
    assert ops.operacion("catalogo").aplicar(ctx).texto() == "python3 main.py catalogo --aplicar"
    assert ops.operacion("correr").verbo == "Correr" and ops.operacion("reporte").verbo == "Simular" and ops.operacion("listar").verbo == "Ejecutar"
    assert [o.id for o in ops.de_grupo("laboratorio")] == ["catalogo", "web", "verificar_todo"]


# ---------------------------------------------------------------------- reingeniería: el espacio de simulación


def test_paleta_lleva_los_colores_del_modelo_a_roles_del_tema():
    assert paleta.rol("#d62728") == "rojo" and paleta.rol("tab:green") == "verde" and paleta.rol("C0") == "azul"
    assert paleta.rol("#ff7f0e") == "dorado" and paleta.rol("purple") == "morado" and paleta.rol("#17becf") == "cian"
    assert paleta.rol("#000000") == "texto" and paleta.rol("#bbbbbb") == "gris" and paleta.rol("k") == "texto"
    assert paleta.rol("", 0) == "azul" and paleta.rol("no-es-un-color", 1) == "rojo"          # por orden, para que dos series no coincidan
    assert paleta.roles(["#2ca02c", "#d62728", "#1f77b4"]) == ["verde", "rojo", "azul"]
    assert set(paleta.ROLES) == {"azul", "rojo", "verde", "dorado", "morado", "cian", "gris", "texto"}


def test_grafico_conserva_la_x_real_y_el_color_de_cada_barra():
    x = [0.0, 0.1, 0.2, 1.0, 5.0, 25.0]                                         # x no uniforme: no se remuestrea
    g = sim.grafico({"lineas": [{"etiqueta": "$Y$", "x": x, "y": [1, 2, 3, 4, 5, 6], "color": "#1f77b4"},
                                {"etiqueta": "cota", "x": [0, 25], "y": [3, 3], "color": "#d62728"},
                                {"etiqueta": "corte", "x": [2, 2], "y": [0, 6], "color": "gray"}],
                     "barras": {"categorias": ["S", "I"], "valores": [3.0, -1.0], "colores": ["#2ca02c", "#d62728"]},
                     "equilibrio": {"x": 1.0, "y": 4.0}, "anotacion": "a\\nb"}, "Tiempo ($t$)", "Producto ($Y$)")
    assert g["lineas"][0]["x"] == x and g["lineas"][0]["rol"] == "azul" and g["lineas"][0]["nombre"] == "Y"
    assert g["horizontales"] == [{"y": 3.0, "nombre": "cota", "rol": "rojo"}] and g["verticales"][0]["x"] == 2
    assert g["barras"]["roles"] == ["verde", "rojo"] and g["equilibrio"] == {"x": 1.0, "y": 4.0}
    assert g["etiquetaX"] == "Tiempo (t)" and g["temporal"] and g["anotacion"] == "a · b" and g["noFinitos"] == 0
    assert g["limites"]["xMin"] == 0 and g["limites"]["xMax"] == 25 and g["limites"]["yMin"] < -1 and g["limites"]["yMax"] > 6
    largo = sim.grafico({"lineas": [{"etiqueta": "l", "x": list(range(5000)), "y": [i * i for i in range(5000)]}]})
    assert len(largo["lineas"][0]["x"]) <= sim.MAX_PUNTOS + 1 and largo["lineas"][0]["x"][-1] == 4999      # ralea, conserva los extremos
    roto = sim.grafico({"lineas": [{"etiqueta": "l", "x": [0, 1, 2], "y": [1, float("nan"), 3]}]})
    assert roto["noFinitos"] == 1 and roto["lineas"][0]["x"] == [0, 2]
    assert sim.unir_limites(g, largo)["xMax"] == 4999 and sim.es_temporal("Periodo") and not sim.es_temporal("Cantidad (Q)")


def test_validez_de_una_corrida():
    corrida = {"resultados": [["Y*", 10.0]]}
    assert sim.validez("verificado", [], corrida)["valido"] is True
    v = sim.validez("diferencias", ["Y* mayor que 1000"], corrida)
    assert not v["valido"] and v["titulo"] == "NO VÁLIDO" and v["nivel"] == "negativo" and "Y* mayor que 1000" in v["texto"]
    v = sim.validez("sin_verificar", [], corrida)
    assert not v["valido"] and v["titulo"] == "SIN VERIFICAR" and v["nivel"] == "neutro"
    v = sim.validez("verificado", [], {"resultados": [["Y*", float("inf")]]})
    assert not v["valido"] and v["titulo"] == "NO VÁLIDO" and "Y*" in v["texto"]               # verificado, pero fuera de dominio
    assert not sim.validez("verificado", [], corrida, no_finitos=2)["valido"]
    assert sim.validez("verificado", [], {})["titulo"] == ""


def test_sensibilidad_barre_el_rango_declarado(laboratorio):
    m = laboratorio.modelo("demo", "d01")
    s = sim.sensibilidad(laboratorio.base(), m, "a", "Q* (cantidad)", n=11)
    assert s["parametro"] == "a" and s["magnitud"] == "Q* (cantidad)" and len(s["x"]) == 11 and not s["fallidos"]
    p = m.parametro("a")
    assert s["x"][0] == pytest.approx(p.minimo) and s["x"][-1] == pytest.approx(p.maximo) and s["valorActual"] == p.valor
    assert s["derivada"] == pytest.approx((s["y"][-1] - s["y"][0]) / (s["x"][-1] - s["x"][0]), rel=1e-6)      # Q* es lineal en a
    assert s["grafico"]["lineas"][0]["nombre"] == "Q* (cantidad)" and s["grafico"]["puntos"][0]["x"] == p.valor
    assert sim.magnitudes([["Q*", 1.0], ["texto", "x"]]) == ["Q*"]


def test_fuentes_solo_donde_la_disciplina_lo_tiene(muestra_sesion, tmp_path):
    o = ops.operacion("fuentes")
    assert o.requiere == "fuentes" and not ops.disponible(o, muestra_sesion.raiz, "demo") and not ops.disponible(o, muestra_sesion.raiz, "")
    (tmp_path / "otra").mkdir()
    (tmp_path / "otra" / "main.py").write_text("def cmd_fuentes(args):\n    pass\n", encoding="utf-8")
    assert ops.disponible(o, tmp_path, "otra") and ops.disponible(ops.operacion("correr"), tmp_path, "")
