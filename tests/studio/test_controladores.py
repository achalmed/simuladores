"""tests/studio/test_controladores.py — los controladores de la ventana en proceso (sin QML) sobre el laboratorio de
muestra: espacio (los filtros y la navegación), modelos (la tabla con su estado, el modelo actual con su ficha, sus
parámetros y escenarios, correr de verdad con el motor, verificar, el escenario propio, los datos exportados),
operaciones (la actual, las órdenes, por qué no se puede, correr y verificar por F5, el plan y la aplicación de lo que
escribe, y, con matplotlib, la CLI real de la disciplina). Nada toca los modelos reales ni catalogo.json."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from conftest import HAY_MATPLOTLIB, requiere_binding


def _esperar(app, tareas, segundos=240):
    inicio = time.monotonic()
    while tareas.activa and time.monotonic() - inicio < segundos:
        app.processEvents()
        time.sleep(0.05)
    app.processEvents()


@pytest.fixture
def piezas(app, muestra_sesion, ajustes_temporales):
    from gui_comun.consola import Consola
    from gui_comun.tareas import Tareas
    from sim_app.controladores.ajustes import Ajustes
    from sim_app.controladores.espacio import Espacio
    from sim_app.controladores.modelos import Modelos
    from sim_app.controladores.operaciones import Operaciones
    consola = Consola()
    tareas = Tareas(consola)
    ajustes = Ajustes()
    espacio = Espacio(consola, ajustes)
    cache = ajustes_temporales / "cache" / "studio"
    modelos = Modelos(espacio, consola, cache=cache, datos=ajustes_temporales / "datos", raiz=muestra_sesion.raiz)
    modelos.verificar_al_abrir = False                  # las pruebas de abajo verifican a mano; el automático, en test_abrir_verifica_y_corre
    operaciones = Operaciones(espacio, modelos, ajustes, consola, tareas, cache=cache)
    yield dict(consola=consola, tareas=tareas, espacio=espacio, modelos=modelos, operaciones=operaciones, ajustes=ajustes, muestra=muestra_sesion, cache=cache)
    _esperar(app, tareas, 10)


@requiere_binding
def test_espacio_filtros_y_navegacion(piezas):
    e, m = piezas["espacio"], piezas["modelos"]
    assert e.disciplina == "" and e.estado == "" and e.nombreNavegacion == "disciplina"
    e.fijarDisciplina("demo")
    assert e.textoDisciplina == "Demostración" and e.nombreNavegacion == "disciplina.demo" and m.modelo.filas == 3 and m.visibles == 3
    e.fijarEstado("verificado")
    assert e.nombreNavegacion == "estado.verificado" and m.modelo.filas == 0 and e.textoFiltro == "Demostración · verificado"
    e.fijarEstado("")
    e.fijarDisciplina("noexiste")
    assert e.disciplina == ""
    assert [x["nombre"] for x in e.entradas_paleta("")][:2] == ["ir.disciplina", "ir.disciplina.demo"]


@requiere_binding
def test_modelos_tabla_y_actual(piezas):
    m = piezas["modelos"]
    assert m.total == 3 and m.resumen == "3 modelos · 1 disciplina · 0 verificados · 0 con diferencias · 3 sin verificar"
    assert [f["texto"] for f in m.filasDisciplinas] == ["Todas", "Demostración"] and m.filasEstados[2]["contador"] == 3
    assert not m.hayActual
    assert m.irA("demo/d01") and m.hayActual and m.cargado and m.id == "d01" and m.textoDisciplina == "Demostración"
    assert m.archivoCorto == "demo/modelos/nivel_01/d01_mercado_lineal.py" and Path(m.archivo).is_file()
    assert [p["nombre"] for p in m.parametros] == ["a", "b", "c", "d"] and m.parametros[0]["unidad"] == "u. m."
    assert [e["nombre"] for e in m.escenarios] == ["base", "mas_demanda", "mas_costo"] and m.escenario == "base"
    assert m.ficha.startswith("# d01 · Mercado lineal") and "## Ecuaciones" in m.ficha
    assert m.estado == "sin_verificar" and m.textoEstado == "Sin verificar"
    assert m.fijarFila(1) is None and m.id == "d02"
    assert not m.irA("demo/d99")
    nombres = [x["texto"] for x in m.entradas_paleta("")]
    assert nombres == ["d01 · Mercado lineal", "d02 · Flujo en barras", "d03 · Capital en el tiempo"]


@requiere_binding
def test_modelos_escenario_corrida_y_verificacion(piezas):
    m, c = piezas["modelos"], piezas["cache"]
    m.irA("demo/d01")
    m.aplicarEscenario("mas_demanda")
    assert m.escenario == "mas_demanda" and m.valores["a"] == 130 and m.textoEscenario == "la demanda autónoma sube de 100 a 130"
    assert "Mecanismo" in m.lecturaEscenario
    m.fijarValor("a", 150)
    assert m.escenario == "propio" and m.valores["a"] == 150
    m.fijarValor("a", 10_000)
    assert m.valores["a"] == 200                                              # al rango del parámetro
    m.restablecer()
    assert m.escenario == "base" and m.valores["a"] == 100
    m.aplicarEscenarioPorIndice(1)
    assert m.correr() and m.hayCorrida and m.nResultados == 3
    g = m.grafico
    assert len(g["lineas"]) == 2 and g["equilibrio"]["x"] == pytest.approx(27.5) and g["etiquetaX"] == "Cantidad (Q)"
    assert m.registro.startswith("# ") and "Q* (cantidad): base 20.0 → 27.5" in m.registro
    assert m.fechaCorrida and (c / "corridas" / "demo-d01.json").is_file()
    fila = m.resultadosModelo.fila(0)
    assert fila["magnitud"] == "Q* (cantidad)" and fila["nivel"] == "positivo"
    assert m.verificar() and m.nVerificaciones == 3 and m.nFallos == 0 and m.estado == "verificado"
    assert m.resumenVerificacion.startswith("3 de 3 verificaciones superadas")
    assert m.contadores["verificado"] == 1 and m.filasEstados[0]["contador"] == 1
    m.irA("demo/d02")
    assert not m.verificar() and m.nFallos == 1 and m.estado == "diferencias"
    assert m.verificacionesModelo.fila(2)["nivel"] == "error" and "esperado > 1000" in m.verificacionesModelo.fila(2)["detalle"]
    assert m.correr() and m.grafico["barras"]["categorias"] == ["S", "I", "G"]
    m.irA("demo/d01")                                                         # la corrida y las verificaciones se releen de la caché
    assert m.hayCorrida and m.escenario == "mas_demanda" and m.nVerificaciones == 3 and m.valores["a"] == 130


@requiere_binding
def test_modelos_escenario_propio_y_datos(piezas, tmp_path):
    m = piezas["modelos"]
    m.irA("demo/d01")
    m.fijarValor("c", 40)
    plan = m.planGuardarEscenario("mi-escenario")
    assert "«mi-escenario»" in plan and "c = 40" in plan
    assert m.guardarEscenario("mi-escenario") and m.escenario == "mi-escenario"
    assert [e["nombre"] for e in m.escenarios][-1] == "mi-escenario" and m.escenarios[-1]["propio"] is True
    archivo = Path(piezas["ajustes"].raiz).parent if False else (tmp_path / "datos" / "escenarios" / "demo-d01.json")
    assert archivo.is_file() and json.loads(archivo.read_text(encoding="utf-8"))["escenarios"][0]["cambios"] == {"c": 40.0}
    m.restablecer()
    m.aplicarEscenario("mi-escenario")
    assert m.valores["c"] == 40
    assert m.correr()
    assert "mi-escenario.csv" in m.planDatos() and m.escribirDatos()
    carpeta = piezas["muestra"].raiz / "demo" / "salidas" / "studio" / "d01"
    assert (carpeta / "mi-escenario.csv").is_file() and json.loads((carpeta / "mi-escenario.json").read_text(encoding="utf-8"))["escenario"] == "mi-escenario"


@requiere_binding
def test_operaciones_f5_y_ctrl_intro(piezas, app):
    o, m, t = piezas["operaciones"], piezas["modelos"], piezas["tareas"]
    assert o.actual == "correr" and o.verbo == "Correr" and not o.puedeSimular and o.motivoNoSimular == "Elige primero un modelo en el catálogo."
    m.irA("demo/d01")
    assert o.puedeSimular and not o.escribe and o.motivoNoAplicar.startswith("Esta operación no tiene modo")
    assert o.simular() and m.hayCorrida and o.plan.startswith("# ")
    o.fijar("verificar")
    assert o.verbo == "Verificar" and o.simular() and m.estado == "verificado"
    o.fijar("guardar_escenario")
    assert o.escribe and o.entradaTipo == "nombre" and o.puedeAplicar
    o.fijarValor("desde-op")
    assert o.simular() and "«desde-op»" in o.plan                              # F5: el plan
    assert o.aplicar() and m.escenario == "desde-op" and "aplicado" in o.registro
    o.fijar("datos")
    assert o.simular() and "desde-op.csv" in o.plan and o.aplicar()
    o.fijar("sensibilidad")
    assert o.entradaTipo == "parametro" and o.valor == "a" and o.ordenSimular == "cd demo && python3 main.py sensibilidad d01 --param a"
    o.fijarValor("b")
    assert o.ordenSimular.endswith("--param b")
    o.fijar("catalogo")
    assert o.ordenSimular == "python3 main.py catalogo --verificar" and o.ordenAplicar == "python3 main.py catalogo --aplicar"
    assert "reescribe catalogo.json" in o.textoConfirmacion
    assert [x["grupo"] for x in o.lista][:1] == ["Modelo"] and o.indiceActual == [x["id"] for x in o.lista].index("catalogo")


@requiere_binding
@pytest.mark.skipif(not HAY_MATPLOTLIB, reason="las CLI de la disciplina necesitan matplotlib")
def test_operaciones_cli_real_de_la_disciplina(piezas, app):
    o, m, t = piezas["operaciones"], piezas["modelos"], piezas["tareas"]
    m.irA("demo/d02")
    o.fijar("verificar_disciplina")
    assert o.sobreDisciplina and o.disciplina == "demo" and o.puedeSimular, o.motivoNoSimular
    terminadas = []
    o.terminada.connect(lambda i, a, c: terminadas.append((i, a, c)))
    assert o.simular()
    _esperar(app, t)
    assert terminadas and terminadas[0][0] == "verificar_disciplina" and terminadas[0][2] == 1, o.plan      # d02 falla a propósito
    assert m.contadores == {"verificado": 2, "diferencias": 1, "sin_verificar": 0}, m.contadores
    assert "verificaciones superadas" in o.plan
    o.fijar("catalogo")
    terminadas.clear()
    assert o.simular()
    _esperar(app, t)
    assert terminadas[0][2] == 0                                                 # el catálogo de la muestra está al día


# ---------------------------------------------------------------------- reingeniería: el espacio de simulación
@requiere_binding
def test_abrir_verifica_y_corre(piezas):
    m = piezas["modelos"]
    m.verificar_al_abrir = True
    m.irA("demo/d01")
    assert m.estado == "verificado" and m.hayCorrida and m.validez["valido"] is True           # al abrir: verificado y corrido
    assert m.graficoBase["lineas"] and m.limitesComunes["xMax"] >= m.grafico["limites"]["xMax"]
    m.irA("demo/d02")
    v = m.validez
    assert m.estado == "diferencias" and not v["valido"] and v["titulo"] == "NO VÁLIDO"
    assert m.grafico["barras"]["roles"] and len(set(m.grafico["barras"]["roles"])) > 1          # las barras con el color de cada una
    m.irA("demo/d03")
    assert m.temporal and m.grafico["temporal"] and m.grafico["horizontales"][0]["nombre"].startswith("estado estacionario")


@requiere_binding
def test_en_vivo_recalcula_al_mover_un_parametro(piezas, app):
    m = piezas["modelos"]
    m.irA("demo/d01")
    antes = m.grafico["equilibrio"]["x"]
    assert m.vivo
    m.fijarValor("a", 150)
    inicio = time.monotonic()
    while m.grafico["equilibrio"]["x"] == antes and time.monotonic() - inicio < 3:
        app.processEvents()
        time.sleep(0.02)
    assert m.grafico["equilibrio"]["x"] > antes and m.escenario == "propio" and m.msCorrida >= 0
    despues = m.grafico["equilibrio"]["x"]
    m.vivo = False
    m.fijarValor("a", 170)
    for _ in range(20):
        app.processEvents()
        time.sleep(0.02)
    assert m.valores["a"] == 170 and m.grafico["equilibrio"]["x"] == despues and not m.vivo     # sin vivo: espera a F5
    assert m.correr() and m.grafico["equilibrio"]["x"] > despues
    m.vivo = True
    assert m.vivo


@requiere_binding
def test_sensibilidad_en_el_controlador(piezas):
    m = piezas["modelos"]
    m.irA("demo/d01")
    assert m.magnitudes[0] == "Q* (cantidad)" and m.parametroSensibilidad == "a"
    assert m.calcularSensibilidad("b", "P* (precio)") and m.parametroSensibilidad == "b" and m.magnitudSensibilidad == "P* (precio)"
    assert len(m.sensibilidad["x"]) == 25 and m.sensibilidad["grafico"]["lineas"]
    assert not m.calcularSensibilidad("no_existe", "")


@requiere_binding
def test_sensibilidad_alrededor_del_escenario_en_edicion(piezas):
    """Con un parámetro movido, el barrido mantiene el escenario (los demás fijos) y la derivada se toma en su valor; sin
    cambios es el de la base (base.sensibilidad, como el CLI). d01: Q* = (a − c) / (b + d)."""
    m = piezas["modelos"]
    m.irA("demo/d01")
    assert m.calcularSensibilidad("a", "Q* (cantidad)")
    base = m.sensibilidad
    assert not base["escenario"] and base["fijos"] == {}
    m.vivo = False                                                    # sin recálculo: solo el barrido
    c0, b, d = m.valores["c"], m.valores["b"], m.valores["d"]
    m.fijarValor("c", c0 + 20)
    m.fijarValor("a", 150)
    assert m.calcularSensibilidad("a", "Q* (cantidad)")
    s = m.sensibilidad
    assert s["escenario"] and s["fijos"] == {"c": c0 + 20} and s["valorActual"] == 150
    assert s["x"] == base["x"]
    for y0, y1 in zip(base["y"], s["y"]):                             # la curva baja 20 / (b + d) en todo el rango
        assert abs((y0 - y1) - 20 / (b + d)) < 1e-6
    assert abs(s["actual"] - (150 - c0 - 20) / (b + d)) < 1e-6 and abs(s["derivada"] - 1 / (b + d)) < 1e-6
    assert s["grafico"]["puntos"][0]["nombre"] == "valor del escenario"
    m.restablecer()
    assert m.calcularSensibilidad("a", "Q* (cantidad)") and not m.sensibilidad["escenario"]
    m.vivo = True


@requiere_binding
def test_un_modelo_lento_se_recalcula_en_un_hilo_aparte(piezas, app, monkeypatch):
    """Un modelo que pasa de TOPE_VIVO_MS no apaga el modo en vivo: el recálculo va a un hilo aparte (la ventana sigue
    atendiendo), de a uno, y solo el último valor pedido se pinta; lo que llega de otro modelo se tira."""
    from sim_app.controladores import modelos as mod
    original = mod.corridas.correr

    def lenta(navegador, modelo, valores):
        time.sleep((mod.TOPE_VIVO_MS + 150) / 1000)
        return original(navegador, modelo, valores)

    monkeypatch.setattr(mod.corridas, "correr", lenta)
    m = piezas["modelos"]
    m.irA("demo/d01")                                                 # la primera corrida, en este hilo, lo mide lento
    assert m.lento and m.vivo
    antes = m.grafico["equilibrio"]["x"]
    m.fijarValor("a", 150)
    inicio = time.monotonic()
    while not m.calculando and time.monotonic() - inicio < 2:          # el temporizador lanza el hilo
        app.processEvents()
        time.sleep(0.01)
    assert m.calculando
    t = time.monotonic()
    app.processEvents()                                               # la ventana no espera al cálculo
    assert time.monotonic() - t < 0.2 and m.grafico["equilibrio"]["x"] == antes
    m.fijarValor("a", 190)                                            # mientras calcula: queda pendiente
    inicio = time.monotonic()
    while (m.calculando or m.valores["a"] != 190 or abs(m.grafico["equilibrio"]["x"] - (190 - m.valores["c"]) / (m.valores["b"] + m.valores["d"])) > 1e-6) \
            and time.monotonic() - inicio < 10:
        app.processEvents()
        time.sleep(0.02)
    q = (190 - m.valores["c"]) / (m.valores["b"] + m.valores["d"])
    assert not m.calculando and abs(m.grafico["equilibrio"]["x"] - q) < 1e-6           # el último pedido, no el 150
    # un cálculo de un modelo que ya no está abierto no se pinta
    m.fijarValor("a", 100)
    inicio = time.monotonic()
    while not m.calculando and time.monotonic() - inicio < 2:
        app.processEvents()
        time.sleep(0.01)
    m.irA("demo/d03")
    m.esperar_hilo()
    for _ in range(10):
        app.processEvents()
        time.sleep(0.02)
    assert m.id == "d03" and m.grafico.get("temporal")


@requiere_binding
def test_operaciones_visibles_segun_la_disciplina(piezas):
    o, m = piezas["operaciones"], piezas["modelos"]
    m.irA("demo/d01")
    assert "fuentes" not in [x["id"] for x in o.lista]                          # L10: la muestra no tiene «main.py fuentes»
    o.fijar("fuentes")
    assert not o.puedeSimular and "no tiene «main.py fuentes»" in o.motivoNoSimular
