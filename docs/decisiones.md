---
tipo: decision
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

- **2026-11-02 · Simuladores Studio es un espacio de trabajo QML + Kirigami sobre `gui-comun` 2.6 (fase 5 de la
  modernización de la familia).** El diseño y sus once decisiones (S1–S11) están en [`rediseno.md`](rediseno.md) §8:
  la tabla sale de `catalogo.json` y el modelo se importa al elegirlo; la navegación es por disciplina y por estado
  de verificación (un estado del studio, con la huella del archivo del modelo); F5 corre y lee con el motor en
  proceso y Ctrl+Intro escribe tras confirmar; un escenario propio es del studio, no del modelo; el gráfico en vivo es
  QuickCharts (`GuiComun.Grafico`, lo que el marco necesitó) y la figura académica sigue siendo la de matplotlib; las
  verificaciones dicen lo que el motor devuelve; un `.venv` del repo sobre el Python del sistema trae `matplotlib`
  (`requirements.txt`; PySide6 nunca); el laboratorio de muestra (`studio/muestra.py`) es lo que prueban y capturan.
  La ventana 1.x de Widgets (`studio/sim_app/ventana.py`, `pagina_modelo.py`) se retira; se lee en la historia de git.

- **2026-11-02 · El motor registra un `matplotlib` vacío cuando no está (`navegador.preparar`), y el studio se apoya
  en eso.** Los `config.py` de las disciplinas importan `matplotlib` para el estilo de sus figuras; con el vacío
  cargan igual, así que correr y verificar un modelo funcionan con el Python del sistema. `graficos` (la figura
  académica) solo se importa cuando se pide, con el `.venv`.
