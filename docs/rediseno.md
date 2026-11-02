---
tipo: doc
estado: hecho
forma: explicacion
titulo: "Rediseño de Simuladores Studio como espacio de trabajo: auditoría de la GUI de Widgets, arquitectura de información, distribución de la ventana, componentes y decisiones"
creado: 2026-11-02
---
# Rediseño de Simuladores Studio: los modelos del laboratorio, sus escenarios y sus verificaciones en una ventana de trabajo

Fase 5 de la modernización de la familia de studios (`gui-comun/docs/arquitectura-qml-kirigami.md` §8): Simuladores
Studio es el séptimo que sigue al piloto Git Studio, cuyo lenguaje visual y arquitectura de información
(`git-studio/docs/rediseno.md` §2, §4, §6, §8) el autor aprobó el 2026-11-01 «para todos los programas de la
familia». Biblioteca y Quarto Studio mostraron cómo se aplica a un studio que orquesta suites con datos propios: la
tabla de lo que se maneja, una operación actual, F5 lee y Ctrl+Intro escribe tras confirmar. Este documento aplica
ese diseño al laboratorio: la auditoría de lo que hay (§1), las ocho preguntas de producto (§2), la arquitectura de
información (§3), la ventana (§4), lo construido (§5), los componentes (§6), lo que el marco necesitó (§7) y las
decisiones (§8). **Está construido** (rama `wip/2026-11-02-qml`, 2026-11-02): las capturas de §5 son reales; pasa a
`hecho` cuando el autor valide el studio en la sesión real sobre los modelos (`../estado.md`).

Tres reglas condicionan todo lo demás. **El rigor es del motor, no de la ventana**: una ficha, un escenario o una
verificación son lo que el modelo declara (`../base.py`: `Ficha`, `Escenario`, `Verificacion`, `Fuente`); la ventana
los muestra, los corre y los compara, nunca los corrige ni los completa. **`catalogo.json` es un contrato generado**
(`../CLAUDE.md`): lo consumen los pubs y `divulgacion`; la ventana lo lee para navegar y solo lo regenera con la CLI del
repo tras confirmar. **Las dependencias del motor no son las de la ventana**: `matplotlib` no está en el Python del
sistema, el único cuyo Qt carga Kirigami; la ventana corre con el `.venv` del repo (§8, S9) y, sin él, enseña el
catálogo y dice qué crear.

## 1. Auditoría de la GUI actual (Widgets, `gui-comun` 1.1)

Una barra lateral con Inicio y una página por disciplina (la marca «Simuladores Studio · Laboratorio computacional»
en la cabecera, retirada en esta fase), construidas a mano con `gui_comun.widgets` y `QtWidgets`. el cargador de disciplinas
(sin Qt) carga cada disciplina a demanda en su espacio de nombres y es lo que esta fase conserva como servicio.

| página | qué hace hoy | entidades y operaciones | lógica separada | mezclado en la ventana |
|---|---|---|---|---|
| Inicio | cuatro cifras (modelos, disciplinas, verificaciones, escenarios) y un mosaico por disciplina | disciplina, modelo | `laboratorio.catalogo` | las cifras pintadas a mano; es un panel de control |
| Macroeconomía · Estadística | los modelos por sección en mosaicos (id, título, pregunta) con un buscador | modelo | `laboratorio.disciplinas` | nada dice si un modelo está verificado ni cuándo corrió |
| Página del modelo | ficha en HTML, ecuaciones y derivación con mathtext, botones de escenario con su lectura, verificaciones (botón «Comprobar»), figura matplotlib incrustada con deslizadores y la tabla de resultados; «Recorrido guiado» abre `app.py` | parámetro, escenario, corrida, verificación | `graficos._dibujar`, `modelo.resultados`, `base.verificar` | la corrida no se guarda ni se exporta; las verificaciones no dicen la fuente ni la diferencia; nada regenera el catálogo; los colores de la figura son los del laboratorio (fondo blanco también en oscuro) |

Lo que falta hoy: la ventana **no dice en qué estado de verificación está cada modelo** (verificado, con diferencias,
sin verificar) ni cuándo corrió por última vez; una corrida se pierde al cerrar; las figuras y los datos de un
escenario no se exportan desde aquí (hay que ir a `main.py reporte`); el catálogo y `navegador.json` no se regeneran
ni se comprueban; el lanzador instalado apunta al Python de Anaconda, que no carga Kirigami, y el Python del sistema no
trae `matplotlib`.

## 2. Las ocho preguntas de producto

1. **Tarea principal**: elegir un modelo, correr un escenario (los del modelo o uno propio moviendo sus parámetros) y
   leer el resultado: las curvas, las magnitudes de equilibrio frente a la base y las verificaciones numéricas contra
   la fuente citada; de paso, saber qué modelos están verificados y exportar figuras y datos para un curso o una
   pieza. El modelo es el sujeto; correr y verificar, los verbos.
2. **Información constante**: cuántos modelos hay por disciplina y cuántos están verificados, con diferencias o sin
   verificar; qué modelo está elegido y qué escenario; si hay una corrida en marcha (barra de estado).
3. **Flujo de trabajo**: navegar por disciplina o por estado de verificación → elegir un modelo en la tabla → leer su
   ficha → elegir o armar un escenario → F5 (corre y lee) → Resultados y Verificaciones → Ctrl+Intro para exportar
   figuras y datos, guardar el escenario o regenerar el catálogo tras confirmar.
4. **Qué se edita y qué se lee**: se leen las fichas, las curvas, los resultados y las verificaciones; se editan los
   parámetros del escenario (en memoria, y como escenario propio del studio si se guarda); la ventana nunca edita un
   modelo, su ficha ni sus verificaciones.
5. **Lo irreversible**: nada de la ventana lo es, pero sí hay escrituras en el repo: `catalogo.json` y
   `navegador.json` (contratos de los pubs), las figuras y los datos exportados en `salidas/` de cada disciplina
   (regenerables, fuera de git). Siempre tras confirmar con la orden exacta.
6. **Qué comparte con la familia**: menú, barra, navegación, tabla, detalles, panel inferior, barra de estado,
   paleta, ajustes, mensajes, `VistaTexto`, `ListaDiagnosticos` (`gui-comun` 2.x); y pidió el gráfico (§7).
7. **Dependencias**: numpy y yaml están en el Python del sistema; `matplotlib` (que importan los `config.py` de las
   disciplinas y el renderizador) no. Decisión S9: un `.venv` del repo sobre el Python del sistema.
8. **Qué queda fuera**: el recorrido guiado de `app.py` (ventana matplotlib propia: se abre desde aquí), las
   animaciones Manim (entorno conda aparte) y la edición de modelos (son archivos Python: el editor).

## 3. Arquitectura de información

### 3.1 Una vista, un modelo actual, un escenario actual, una operación actual

- **Navegación** (`PanelNavegacion`): *Disciplinas* (Todas, Macroeconomía, Estadística, con contador) y *Verificación*
  (Verificados, Con diferencias, Sin verificar, con contador). Elegir una fila filtra la tabla.
- **Centro** (`TablaDatos`): un modelo por fila: id, modelo, sección (nivel), parámetros, escenarios, verificaciones,
  estado (semántico), última corrida. Filtro Ctrl+F sobre id, título, sección y pregunta. Orden por cabecera.
- **Detalles** (`PanelDetalles` del modelo actual): Ficha · Escenario · Resultados · Verificaciones · Registro ·
  Operación.
- **Panel inferior** (`PanelInferior`): la salida del motor (lo que escribe una corrida en proceso o la CLI de la
  disciplina) y el progreso de una tarea.
- **Barra de estado**: «139 modelos · 2 disciplinas · N verificados · N con diferencias · N sin verificar» y, a la
  derecha, el modelo actual con su escenario y la operación elegida.

### 3.2 Entidades y dónde vive cada dato

| entidad | de dónde sale | qué muestra la ventana |
|---|---|---|
| disciplina | las carpetas con `config.py`, `main.py` y `modelos/` (`laboratorio.disciplinas`); su nombre, `AREA` y `SECCIONES` del `config` | la navegación; el grupo de la paleta |
| modelo | `catalogo.json` para la tabla (sin importar nada); el `Modelo` importado al elegirlo (`laboratorio.modelo`) | la fila; la ficha en Markdown; sus parámetros, escenarios y verificaciones |
| parámetro | `Parametro` (nombre, valor, mínimo, máximo, paso, etiqueta, grupo, definición, unidad) | el formulario del escenario, agrupado por `grupo` |
| escenario | `Escenario` del modelo (cambios, lectura, cadena) y los **propios del studio** (`$XDG_DATA_HOME/simuladores-studio/escenarios/<disciplina>-<id>.json`) | el selector del escenario; la lectura y el mecanismo |
| corrida | `navegador.calcular` (curvas y resultados con los valores pedidos) en proceso; se guarda en la caché del studio (`corridas/<disciplina>-<id>.json`) | el gráfico; las series; las magnitudes base frente al escenario (Δ, Δ %) |
| verificación | `base.verificar` (la coherencia estructural más las del modelo) y `fuentes.comprobar` si la ficha cita; el resultado en la caché (`verificaciones.json`) con la fecha y la huella del archivo del modelo | `ListaDiagnosticos`: nombre, detalle (valor, esperado, diferencia), fuente, archivo; el estado del modelo |
| estado de verificación | *verificado* (todas pasaron y el archivo no cambió desde entonces), *con diferencias* (alguna falló), *sin verificar* (nunca, o el archivo cambió) | la columna Estado, la navegación, la barra de estado |
| figura y datos | `graficos.figura` (PNG académico) y las series en CSV/JSON en `salidas/<nivel>/<id>/` de la disciplina | la pestaña Resultados muestra el PNG si se pide; exportar escribe tras confirmar |
| catálogo | `catalogo.json` y `navegador.json` (GENERADOS por `main.py`) | `catalogo --verificar` en F5; `--aplicar` en Ctrl+Intro |

### 3.3 Dónde vive cada operación

Cada operación existe una sola vez en `Acciones` (`studio/sim_app/aplicacion.py`) y su catálogo es
`studio/sim_app/servicios/operaciones.py`: lo que lee (F5) y lo que escribe (Ctrl+Intro tras confirmar).

| grupo | F5 lee o corre | Ctrl+Intro escribe tras confirmar |
|---|---|---|
| Modelo | **Correr el escenario** (en proceso: curvas y resultados; la corrida a la caché del studio) · **Verificar el modelo** (en proceso: `base.verificar` y las citas) · Sensibilidad (`main.py sensibilidad <id> <parámetro>`) · Comparar escenarios (`main.py comparar <id> …`) · Ficha en la terminal (`main.py ficha <id>`) | **Exportar figuras y datos** (`main.py reporte <id>` más las series del escenario en CSV y JSON en `salidas/`) · **Guardar el escenario** (los valores actuales como escenario propio del studio) |
| Disciplina | **Verificar la disciplina** (`main.py verificar`: la salida en el panel inferior; los estados de todos sus modelos se actualizan) · Comprobar las citas (`main.py fuentes`, estadística) · Listar (`main.py listar`) | — |
| Laboratorio | **Comprobar el catálogo** (`main.py catalogo --verificar`) · Comprobar el navegador (`main.py web --verificar`) · Verificar todo (`main.py verificar`) | **Regenerar el catálogo** (`main.py catalogo --aplicar`) · Regenerar el navegador (`main.py web --aplicar`) |
| Herramientas | Recorrido guiado (`main.py app` de la disciplina, ventana propia) · El entorno del studio… · Instalar el acceso directo | — |

## 4. Distribución de la ventana (1280 × 800)

Menú (Archivo · Editar · Ver · Modelo · Disciplina · Laboratorio · Herramientas · Ajustes · Ayuda), barra corta
(Correr F5 · Exportar Ctrl+Intro · | · Verificar · el selector de operación · el filtro), navegación compacta a la
izquierda, la tabla de modelos en el centro, los detalles del modelo a la derecha (Ficha, Escenario, Resultados con
el gráfico, Verificaciones, Registro, Operación), el panel inferior con la salida del motor y la barra de estado con
los contadores por estado. Ningún nombre ni logotipo dentro de la ventana; ningún color ni fuente propios.

## 5. Lo construido

| captura | qué muestra |
|---|---|
| `figuras/simuladores-studio-oscuro.png` | Lliphi Oscuro: el laboratorio de muestra, el modelo elegido tras correr su escenario, la pestaña Resultados con el gráfico (QuickCharts) y las magnitudes |
| `figuras/simuladores-studio-claro.png` | Lliphi Claro: la pestaña Verificaciones con cada comprobación, su detalle y su fuente |
| `figuras/simuladores-studio-paleta.png` | la paleta de órdenes (Ctrl+K) buscando un modelo |

Las capturas se toman sobre el laboratorio de muestra (`studio/muestra.py`), con HOME, configuración y caché
temporales (ninguna ruta de la máquina en pantalla), con `studio/capturar.py`.

## 6. Componentes

`VentanaStudio` (menú, barra, navegación, centro, detalles, inferior, estado, paleta, ajustes), `PanelNavegacion`,
`TablaDatos`, `PanelDetalles`, `PanelInferior`, `VistaTexto` (la ficha en Markdown), `ListaDiagnosticos` (las
verificaciones), `Grafico` (§7), `MenuAcciones`, `BotonAccion`, `DialogoAjustes`, `PaletaOrdenes`, `Mensajes`;
`Kirigami.FormLayout` para el escenario generado desde los parámetros; `Kirigami.PromptDialog` para confirmar.

## 7. Lo que el marco necesitó (`gui-comun` 2.6.0)

- **`Grafico`** (`org.kde.quickcharts`): líneas (series `{nombre, y}` sobre una rejilla común de x, con etiquetas de
  los ejes, rejilla, leyenda, puntos marcados y el equilibrio) o barras (`{categorias, valores}`); los colores de las
  series salen de la paleta de QuickCharts (`ColorGradientSource` sobre el acento de `Kirigami.Theme`), nunca de una
  lista propia; si el módulo no está, muestra la imagen (`imagen`, un PNG) y, sin ella, un mensaje de vacío. Página
  en la galería y pruebas.

## 8. Decisiones

- **S1 · La tabla sale del catálogo y el modelo se importa al elegirlo.** `catalogo.json` describe los 139 modelos sin
  importar nada (abrir es instantáneo); el `Modelo` se importa con su disciplina activa (`laboratorio.py`, que ya
  aislaba los espacios de nombres), y `graficos` solo cuando se pide la figura académica (así la ventana corre sin
  `matplotlib`).
- **S2 · La navegación es por disciplina y por estado de verificación**, no por sección: hay 12 secciones en macro y
  otras tantas en estadística; la sección es una columna (orden y filtro). Las secciones siguen en la paleta y en el
  grupo del modelo.
- **S3 · El estado de verificación es del studio**, con fecha y huella del archivo del modelo: «verificado» caduca
  cuando el archivo cambia; nada del estado se escribe en el repo (caché del studio). `main.py verificar` de una
  disciplina actualiza los estados de todos sus modelos desde su salida (`✔`/`✘` por modelo).
- **S4 · F5 corre y lee; Ctrl+Intro escribe tras confirmar.** Correr un escenario calcula en proceso con el motor
  (`navegador.calcular`: lo que ya ejecuta el navegador de los pubs) y escribe solo la caché del studio; exportar
  figuras y datos, guardar un escenario y regenerar el catálogo o el navegador muestran la orden exacta y lo que
  tocan, y corren solo si se confirma. Las CLI de las disciplinas corren con `gui_comun.tareas.proceso`.
- **S5 · Un escenario propio es del studio, no del modelo.** Guardar los valores actuales los deja en
  `$XDG_DATA_HOME/simuladores-studio/escenarios/`; añadir un escenario al modelo es editar su archivo, y eso lo hace el
  editor (el autor) con su lectura y su cadena.
- **S6 · El gráfico en vivo es QuickCharts; la figura académica es la de matplotlib.** QuickCharts posiciona cada
  serie por índice, así que las curvas se remuestrean sobre una rejilla común de x (interpolación lineal, 200
  puntos) y las líneas verticales u horizontales (una x o una y constante) se dibujan como marcas; las barras van a
  `BarChart`. La figura de `graficos.figura` (fondo blanco, paleta del laboratorio, etiquetas anti-solape) es la que
  se exporta y la que se muestra con «Ver la figura académica».
- **S7 · Las ecuaciones se leen en la ficha.** La ficha es Markdown (`VistaTexto`): contexto, autores, supuestos,
  variables, ecuaciones (cada una con su LaTeX y su significado), derivación, intuición, equilibrio, limitaciones,
  evolución, procedencia y fuentes. Con el `.venv`, cada ecuación se dibuja con mathtext (como en 1.x) a un PNG de
  la caché y la ficha la incrusta; sin él, se lee el LaTeX.
- **S8 · Las verificaciones dicen valor, esperado, fuente y diferencia** tal como el motor las devuelve
  (`detalle` de cada `Verificacion`) más la procedencia de la ficha y, en estadística, el resultado de
  `fuentes.comprobar` por cita (verificada, aviso, falla o no comprobable sin la biblioteca).
- **S9 · Un `.venv` del repo sobre el Python del sistema** (`/usr/bin/python3 -m venv --system-site-packages .venv` y
  `pip install -r requirements.txt`: `matplotlib`; numpy y yaml ya están): ve el PySide6 y el Kirigami del sistema y
  añade lo que el motor necesita; `main.py`, `install.sh` y el `.desktop` lo usan si existe y, si no, avisan qué
  crear. PySide6 nunca se instala en el `.venv`; nada de `sudo` ni `apt`.
- **S10 · El laboratorio de muestra** (`studio/muestra.py`): el motor real (`base.py`, `navegador.py`, `main.py`…)
  copiado a una carpeta temporal con una disciplina `demo` de dos modelos (uno que pasa sus verificaciones y otro con
  una diferencia) cuyo `config.py` no importa `matplotlib`; `SIMULADORES_STUDIO_RAIZ` apunta ahí. Las pruebas y las
  capturas corren sobre él; una corrida real del motor siempre, y la CLI de la disciplina solo si hay `matplotlib`.
- **S11 · Rutas por `core/env.py`**: `SIMULADORES_DIR` es la raíz por omisión y `CORE_PYTHON` el intérprete de las
  CLI cuando no hay `.venv`; ninguna ruta de la máquina en el código ni en pantalla.
