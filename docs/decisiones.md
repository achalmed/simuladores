---
tipo: decision
forma: explicacion
titulo: 'Decisiones de simuladores'
estado: activo
---
# Decisiones de simuladores

Registro único y acumulativo de por qué el repositorio es como es. Cada entrada lleva su fecha; una decisión revocada
no se borra: se marca «Superada por …». Lo que se hizo en una sesión va al mensaje de commit, no aquí; lo pendiente, a
[`estado.md`](../estado.md) §Por hacer. Las decisiones del motor y de cada disciplina siguen en sus documentos de
diseño (`macro/docs/laboratorio-macro.md`, `estadistica/docs/laboratorio-estadistica.md`); aquí, las del repo y las
de la ventana.

## La ventana

- **2026-11-03 · La sensibilidad sigue al escenario y un modelo lento se calcula en un hilo, sin apagar el modo en vivo.**
  El barrido de la ventana mantiene los demás parámetros del escenario en edición y toma la derivada en su valor
  (`studio/sim_app/servicios/simulacion.py`); sin cambios es `base.sensibilidad` del motor, que no se tocó (contrato del
  CLI y de los pubs). Los 139 modelos del repo se midieron con `studio/medir.py` (la corrida del recálculo en vivo, con
  sus valores por omisión): solo e26 pasa de 400 ms (unos 410). En vez de apagarle el modo en vivo, su recálculo corre en
  un hilo aparte, de a uno, con un testigo por modelo: lo que llega de otro modelo o de valores ya cambiados no se
  pinta. Python no calcula más rápido en un hilo (el GIL): lo que se gana es que la ventana no se detenga.

- **2026-11-02 · Simuladores Studio es un laboratorio de simulación sobre `VentanaBase` de `gui-comun` 3.0
  (reingeniería de los diez studios, §3.8).** El diagnóstico, la distribución y sus doce decisiones (L1–L12) están en
  [`reingenieria.md`](reingenieria.md): el área central es el espacio de simulación y no una tabla; el gráfico es
  propio (Canvas) porque QuickCharts sitúa cada valor por su índice y obligaba a remuestrear las curvas; los colores
  del modelo se llevan a roles del tema; mover un parámetro recalcula en vivo cuando el modelo es rápido; y una corrida
  solo se presenta como válida si el modelo está verificado y sus números son finitos. Supera, en la distribución y en
  el gráfico, a la entrada siguiente (S1–S11 de `rediseno.md`); el resto de aquella sigue.

- **2026-11-02 · Simuladores Studio es un espacio de trabajo QML + Kirigami sobre `gui-comun` 2.6 (fase 5 de la
  modernización de la familia).** *Superada en la distribución y el gráfico por la entrada anterior.* El diseño y sus once decisiones (S1–S11) están en [`rediseno.md`](rediseno.md) §8:
  la tabla sale de `catalogo.json` y el modelo se importa al elegirlo; la navegación es por disciplina y por estado
  de verificación (un estado del studio, con la huella del archivo del modelo); F5 corre y lee con el motor en
  proceso y Ctrl+Intro escribe tras confirmar; un escenario propio es del studio, no del modelo; el gráfico en vivo es
  QuickCharts (`GuiComun.Grafico`, lo que el marco necesitó) y la figura académica sigue siendo la de matplotlib; las
  verificaciones dicen lo que el motor devuelve; un `.venv` del repo sobre el Python del sistema trae `matplotlib`
  (`requirements.txt`; PySide6 nunca); el laboratorio de muestra (`studio/muestra.py`) es lo que prueban y capturan.
  La ventana 1.x de Widgets (`ventana.py` y `pagina_modelo.py` de `studio/sim_app/`) se retira; se lee en la historia de git.

- **2026-11-02 · El motor registra un `matplotlib` vacío cuando no está (`navegador.preparar`), y el studio se apoya
  en eso.** Los `config.py` de las disciplinas importan `matplotlib` para el estilo de sus figuras; con el vacío
  cargan igual, así que correr y verificar un modelo funcionan con el Python del sistema. `graficos` (la figura
  académica) solo se importa cuando se pide, con el `.venv`.
