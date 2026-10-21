---
tipo: readme
estado: activo
---
# simuladores/ — el laboratorio computacional (multi-disciplina)

<!-- suite:inicio -->
**Suite `simuladores`** · objetivo *publicacion* · estado *activo* · python · interfaz cli+gui

Laboratorio computacional: cada teoría o método como modelo ejecutable (ficha pedagógica, escenarios, verificaciones numéricas) que consumen docencia, divulgacion y los pubs por catalogo.json y, en el navegador (Pyodide), por navegador.json.

- Escribe en: archivos · simula por defecto: no
- Entrada: los modelos de <disciplina>/modelos/nivel_NN/; datos reales de datafw por DATAFW_DIR (nivel 12 de macro)
- Depende de: python3 con numpy, matplotlib y yaml (el de anaconda base; el del sistema no trae matplotlib), manim (conda manim-datafw; solo estadistica/animaciones), core/env.py (DATAFW_DIR), core/py-common/biblioteca.py (fuentes.py comprueba las citas contra Calibre)
- Nota: Repo propio desde 2026-10-20 (antes docencia/simuladores, con su historia). catalogo simula por defecto (imprime) y escribe catalogo.json solo con --aplicar; reporte escribe en <disciplina>/salidas/ (regenerable, fuera de git) sin pedir --aplicar. La app (sin argumentos) abre la GUI matplotlib. web simula por defecto y escribe navegador.json (los modelos que corren en el navegador con Pyodide) solo con --aplicar.

Comandos:

```bash
main.py catalogo [--aplicar | --verificar]
main.py verificar
main.py web [--aplicar | --verificar]
macro/main.py [app | listar | ficha <m> | simular <m> | comparar <m> | sensibilidad <m> <p> | reporte <m> | verificar]
estadistica/main.py [app | listar | fuentes | ficha <e> | simular <e> | reporte <e> | verificar]
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-21); no se edita a mano.</sub>
<!-- suite:fin -->

<!-- suites:inicio -->
Suites de esta carpeta (1); índice global en `meta/INDICE_SCRIPTS.md`. Patrón: M main · C config · L lib.

| Suite | Carpeta | Objetivo | Escribe en | Simula | Timer | Estado | Patrón |
|---|---|---|---|---|---|---|---|
| `simuladores` | [simuladores](./) | publicacion | archivos | no |  | activo | `M··` |

<sub>Bloque generado desde los `suite.yml` por `core/suites.py generar` (2026-10-21); no se edita a mano.</sub>
<!-- suites:fin -->

Laboratorio histórico y computacional de economía y sus herramientas: cada teoría o método reconstruido como
**modelo ejecutable** con ficha pedagógica (contexto histórico → derivación → intuición → limitaciones), simulación de
escenarios y **verificación numérica de sus teoremas**. Repo propio desde el 2026-10-20 (antes `docencia/simuladores`,
y antes `datafw/simuladores`; la historia viaja con él). Se encuentra por `SIMULADORES_DIR` de `core/env.py`.

Es **un solo laboratorio con varias disciplinas hermanas** que comparten un motor común. El motor (agnóstico a la
disciplina) vive en la raíz, con la aplicación (`app.py`); cada disciplina es una subcarpeta con su `config.py`, su
`main.py` y sus `modelos/`.

## Uso

```bash
cd ~/Documents/simuladores
python3 main.py verificar                  # verificar de todas las disciplinas (salida 0 solo si todas pasan)
python3 main.py catalogo                   # el catálogo de modelos por stdout (simula: no escribe)
python3 main.py catalogo --aplicar         # escribe catalogo.json, el contrato que leen los pubs
python3 main.py catalogo --verificar       # 0 si catalogo.json está al día con los modelos
python3 main.py web                        # qué modelos corren en el navegador y cuáles no, con su motivo (simula)
python3 main.py web --aplicar              # escribe navegador.json, el contrato del laboratorio en el navegador
python3 main.py web --verificar            # 0 si navegador.json está al día

cd macro       && python3 main.py          # abre el laboratorio macro (la app)
cd macro       && python3 main.py verificar
cd estadistica && python3 main.py fuentes  # citas comprobadas contra la edición (Calibre)
```

Cada disciplina tiene su propio punto de entrada; su `main.py` añade la raíz al `sys.path` para reusar el motor.

### Las capas de visualización (un modelo, tres vistas)

El **modelo nunca se mezcla con la interfaz**. La misma lógica (`base.py`) se muestra de tres formas:

| Vista | Herramienta | ¿En vivo? | Para qué |
|---|---|---|---|
| Estática | matplotlib | figura | reportes (`reporte`), ver el estado |
| Interactiva / animada | matplotlib (`Slider`/`FuncAnimation`) | **sí, en la app** | explorar: mover parámetros y ver en tiempo real |
| Video pulido | **Manim** (env conda aparte) | archivo | redes / clases / incrustar (ver `estadistica/animaciones/`) |
| Navegador | **Pyodide** + SVG (en `web/_aula`) | **sí, en la página del pub** | mover parámetros sin instalar nada |

### En el navegador (Pyodide)

La página `/laboratorio/<id>/` de cada pub ejecuta el MISMO modelo en el navegador: Pyodide y numpy se descargan
(versión exacta, desde jsDelivr), el navegador escribe en su sistema de archivos los `.py` mínimos e importa el
`MODELO` como el escritorio. Nada se reescribe en JavaScript. Las piezas:

- `navegador.py` (motor): registra un `matplotlib` vacío (los `config.py` lo importan para el estilo de escritorio) y
  serializa `curvas` y `resultados` a JSON estricto; lo usan el exportador y el navegador.
- `main.py web --aplicar` → `navegador.json`: por modelo, sus archivos (`base.py`, `navegador.py`, `config.py` de la
  disciplina, los `__init__.py` y el módulo con sus auxiliares, por análisis estático de sus `import`), parámetros,
  escenarios, ficha y la vista inicial (los valores por defecto ya calculados, para la figura sin JavaScript).
- Quedan fuera, con su motivo, los modelos que importan algo más que numpy y la biblioteca estándar sin archivos (el
  nivel 12 de macro, que lee las series del BCRP de datafw) y los que tardan más de 0,3 s de CPU por cálculo (hoy e26).
  Hoy corren 120 de 139.

## Estructura

```
simuladores/
├── main.py         el laboratorio entero: catalogo (catalogo.json) y verificar de todas las disciplinas
├── base.py         MOTOR: dataclasses (Modelo/Ficha/Escenario/Verificacion), cálculo y verificación
├── graficos.py     render matplotlib con anti-solape y dibujo progresivo
├── laboratorio.py  láminas de experimento
├── reporte.py      informe MD por modelo
├── app.py          la aplicación (recorrido pedagógico) que usan todas las disciplinas
├── fuentes.py      comprueba cada cita (calibre_id, hoja del PDF, pasaje) contra la edición
├── catalogo.json   GENERADO por main.py catalogo --aplicar: id, título, área, nivel, parámetros, escenarios, ficha resumida
├── navegador.py    adaptador del navegador (Pyodide): matplotlib vacío y serialización JSON de curvas y resultados
├── navegador.json  GENERADO por main.py web --aplicar: los modelos que corren en el navegador, sus .py y su vista inicial
├── macro/          Macroeconomía — currículo completo por niveles (docs/laboratorio-macro.md)
└── estadistica/    Estadística — en curso (temario.yml, docs/laboratorio-estadistica.md, animaciones Manim)
```

Cada disciplina guarda sus modelos por nivel (`modelos/nivel_NN/`), su `matriz_trazabilidad.csv`, su `docs/` y sus
`salidas/` (regenerables, fuera de git). Cuántos modelos y verificaciones tiene cada una lo dice `main.py verificar`.

**Añadir una disciplina:** `simuladores/<disciplina>/` con `config.py` (rutas, paleta, `SECCIONES`, `AREA`,
`PROCEDENCIA_POR_DEFECTO`), `main.py` (bootstrap que añade la raíz al path + CLI) y `modelos/nivel_NN/`. **Prohibido
copiar el motor**: se importa de la raíz. `main.py catalogo` la descubre sola.

## Consumidores

| quién | qué usa | qué no puede cambiar sin avisar |
|---|---|---|
| `docencia` | `scripts/enlazar.py simuladores` y `verificar` (recursos `{tipo: simulador}` de `curso.yml`) | rutas `<disciplina>/modelos/nivel_NN/<id>_slug.py`; `id` y `nombre` de cada modelo |
| `divulgacion` | `divulgacion/lib/simuladores.py` importa el modelo (`simuladores: [macro/m04]`) | `Modelo.curvas/parametros/escenarios/verificaciones/ecuaciones_calibradas/ficha` |
| los pubs (fase 4 de la plataforma educativa) | `catalogo.json` | sus campos (sube `esquema` si cambian) |
| la vitrina de los pubs en el navegador (`web/_aula`) | `navegador.json`, `navegador.py` y los `.py` que lista | sus campos (sube `ESQUEMA_WEB`); `navegador.calcular_json` |

## Límite honesto

- Licencia: el código y las fichas de los modelos son MPL-2.0 (`LICENSE`), como el código del resto del ecosistema;
  repositorio público desde el 2026-10-20 (decisión del autor).

- Es un laboratorio pedagógico: los modelos reproducen teoremas y escenarios de manual, no pronósticos. Los que usan
  datos reales (el nivel 12 de macro, con series del BCRP) los leen de `datafw` por nombre; el laboratorio no adquiere datos.
- «Página verificada» significa que el pasaje citado está en esa hoja del PDF del `calibre_id`: lo comprueba
  `fuentes.py` con el texto que da `core/py-common/biblioteca.py`. Sin la biblioteca en la máquina, la cita queda
  «no comprobable», no verificada; y la página impresa solo se confirma si el PDF trae el folio en su texto.
- `catalogo.json` describe los modelos, no los ejecuta: las cifras de un escenario se calculan con el modelo. Los
  `cursos` del catálogo salen del `temario.yml` de cada disciplina: completo en estadística; en macro, parcial (solo
  IS-LM, el tema que ningún `curso.yml` enlazaba); la vitrina une además los recursos `{tipo: simulador}` de los `curso.yml`.
- En el navegador, el cálculo es el de numpy 2.2 de Pyodide (en el escritorio, el numpy instalado): con la misma semilla
  los resultados de IS-LM y del TCL coinciden con los de CPython; la primera carga pide unos 12 MB.
- Sin remoto: publicar el repo es decisión del autor.
