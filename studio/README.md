---
tipo: readme
estado: activo
---
# studio/ — Simuladores Studio, la ventana del laboratorio (QML + Kirigami sobre gui-comun 2.6)
<!-- suite:inicio -->
**Suite `simuladores_studio`** · objetivo *publicacion* · estado *activo* · python · interfaz gui

Ventana del laboratorio (QML + Kirigami sobre gui-comun 2.6): los modelos de cada disciplina con su estado de verificación, su ficha, su escenario (formulario desde los parámetros), su corrida con el gráfico (QuickCharts) y las magnitudes frente a la base, y sus verificaciones con su fuente; F5 corre y lee con el motor, Ctrl+Intro exporta figuras y datos, guarda un escenario propio o regenera el catálogo tras confirmar.

- Escribe en: archivos · simula por defecto: sí
- Depende de: /usr/bin/python3 con PySide6 del sistema (python3-pyside6.*), Kirigami (qml6-module-org-kde-kirigami) y QuickCharts (qml6-module-org-kde-quickcharts), gui-comun 2.6 (módulo QML GuiComun, Grafico), .venv del repo con matplotlib para la figura académica, las fórmulas, los reportes y las CLI (requirements.txt; opcional), el motor del repo (base.py, navegador.py) y los modelos de cada disciplina, sin copiarlos
- Nota: No edita ningún modelo: correr y verificar calculan en proceso y escriben solo la caché del studio; exportar (salidas/ de la disciplina), guardar un escenario propio (datos del studio) y regenerar catalogo.json o navegador.json piden confirmación con la orden exacta.

Comandos:

```bash
main.py
main.py --smoke
../install.sh
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-11-02); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

La ventana de trabajo del laboratorio, al estilo Dolphin/Kate (`../docs/rediseno.md`): la tabla de modelos de
`catalogo.json` con su estado de verificación y su última corrida, filtrada por disciplina o por estado desde la
navegación; el modelo elegido en el panel de detalles con su **Ficha** (Markdown; con el `.venv`, las ecuaciones
dibujadas con mathtext), su **Escenario** (el selector con los del modelo y los propios del studio, y el formulario
generado desde sus parámetros), sus **Resultados** (el gráfico en vivo de QuickCharts, o la figura académica de
matplotlib con Ctrl+G, y las magnitudes frente a la base), sus **Verificaciones** (cada identidad o teorema con su
detalle y su fuente) y su **Registro**; el panel inferior con la salida del motor; la paleta (Ctrl+K) encuentra
cualquier modelo u operación.

**F5 corre y lee; Ctrl+Intro escribe tras confirmar.** Correr el escenario y Verificar el modelo calculan en proceso
con el motor (`navegador.calcular`, `base.verificar`) y escriben solo la caché del studio; lo demás es la CLI del
laboratorio (`main.py` de la disciplina o de la raíz) en el panel inferior. Exportar el reporte y las figuras, exportar
los datos del escenario, guardar un escenario propio y regenerar `catalogo.json` o `navegador.json` muestran la orden
exacta y lo que tocan, y corren solo si se confirma. El rigor es del motor: la ventana no edita ningún modelo.

## Uso

```bash
cd ~/Documents/simuladores
/usr/bin/python3 -m venv --system-site-packages .venv && .venv/bin/pip install -r requirements.txt   # una vez: matplotlib
/usr/bin/python3 studio/main.py            # (se relanza con .venv/bin/python si existe)
./install.sh                               # el acceso directo del menú (-n simula)
tests/run.sh                               # las pruebas del studio sobre el laboratorio de muestra
/usr/bin/python3 studio/capturar.py salida.png --esquema ~/Documents/lliphi/generado/esquema/LliphiOscuro.colors --modelo demo/d01 --pestana 2
```

Sin el `.venv` la ventana corre igual (correr y verificar un modelo: el motor registra un `matplotlib` vacío, como en
el navegador), pero no hay figura académica, fórmulas dibujadas, reportes ni CLI del laboratorio; avisa qué crear
(Herramientas › El entorno del studio…). PySide6 nunca va en el `.venv`: es el del sistema, el único que carga Kirigami.

## Estructura

```
studio/
├── main.py                 sin lógica: relanza con el .venv si existe y arranca sim_app.aplicacion
├── muestra.py · capturar.py   el laboratorio de muestra (motor real + disciplina demo) y las capturas sobre él
└── sim_app/
    ├── aplicacion.py       construir(): controladores y Acciones (menú, barra, paleta, atajos); Main.qml
    ├── servicios/          sin Qt: rutas, laboratorio (disciplinas aisladas), corridas, verificaciones, fichas, formulas, operaciones
    ├── controladores/      espacio (filtros), modelos (tabla, modelo actual, corrida, verificaciones), operaciones, ajustes
    └── qml/                Main.qml sobre GuiComun.VentanaStudio y componentes/ (Ficha, Escenario, Resultados, Verificaciones, Registro, Operación)
```

Los estados de verificación y las corridas viven en la caché del studio (`$XDG_CACHE_HOME/simuladores-studio/`); los
escenarios propios, en `$XDG_DATA_HOME/simuladores-studio/escenarios/`; nada de eso entra en el repo.

## Límite honesto

- **QuickCharts posiciona cada valor por su índice**: las curvas se remuestrean sobre una rejilla común de x
  (interpolación lineal) y una línea con x o y constante se dibuja como marca; la figura académica es la de siempre.
- **Sin pantalla, QuickCharts no pinta con el renderizador por software**: las capturas y la galería usan
  `QT_QUICK_BACKEND=rhi`; las pruebas sin pantalla comprueban que carga sin errores, no que dibuje.
- **El recorrido guiado** (`main.py app`) se abre en su propia ventana matplotlib; no está dentro del studio.
