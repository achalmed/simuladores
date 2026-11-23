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

## El motor

- **2026-11-24 · La ficha pedagógica: resultados de aprendizaje y ejercicios del alumno, dentro de la ficha y
  comprobados contra el modelo** (fase 3.3 del plan «aprender y enseñar»; diseño completo y sustento en
  [`pedagogia.md`](pedagogia.md)).
  1. **Vive en el modelo** (`Ficha.pedagogia`, `base.Pedagogia` con `Resultado` y `Ejercicio`), no en un YAML al lado
     ni en docencia. Así hay una sola fuente por simulador, viaja con él a divulgacion y al navegador, y su clave se
     comprueba en la misma corrida que sus verificaciones. Alternativa descartada: un `pedagogia.yml` por modelo, que
     el autor o `05/03` podrían escribir sin Python, pero que se desfasaría del modelo sin que nada lo notara. El
     campo es opcional y `None` por omisión: los 136 modelos sin ficha pedagógica no cambian, y la interfaz que lee
     divulgacion tampoco.
  2. **El vocabulario es el de docencia**: el nivel del resultado, de la taxonomía SOLO (§10.1); la predicción
     cerrada, un ítem del banco §10.2 tal cual (`tipo`, `opciones`, `respuesta`, `errores` por distractor, `bloom`…).
     Como el motor no lee otros repos, `pedagogia.py` copia la regla del ítem; una prueba la compara con la de
     `docencia/scripts/alineamiento.py` cuando ese repo está, y pasa los ítems por su `quiz_aula`.
  3. **Un ejercicio, dos ítems**: la predicción cerrada (el aula la corrige sola y retroalimenta por distractor) y la
     explicación abierta (la puesta en común). Elegir una opción o mover un control solo es activo; predecir y
     explicar por escrito es constructivo (Chi y Wylie, 2014, pp. 222 y 224).
  4. **La clave es una aserción**: `espera` y `valores` dicen la respuesta esperada en direcciones y cifras de
     `resultados()`, y `base.verificar` suma «ficha pedagógica (resultados y ejercicios)», que falla si el modelo dice
     otra cosa. Como con las citas de `fuentes.py`, la afirmación del docente se vuelve comprobable.
  5. **Lo propuesto por la IA no sale al alumno** (C3.3): `catalogo.json` y `navegador.json` llevan
     `ficha.pedagogia` solo si `origen.verificacion` es `verificada`, y nunca las claves del docente (como la vitrina
     del aula deja fuera `respuesta` y `explicacion` del banco). Los dos contratos suben a `esquema` 2 aunque hoy su
     contenido no cambie.
  6. **El resultado es del simulador** («r1»): un mismo simulador sirve a varios cursos, y cada curso lo traduce a su
     `raN` al pegar los ítems en su banco (`main.py pedagogia REF --formato banco`). El simulador no escribe en
     docencia.

## La ventana

- **2026-11-18 · Simuladores Studio toma su forma propia, el laboratorio, con los colores del tema y los avisos en
  Plasma.** El autor aprobó para los diez programas de la familia una forma propia cada uno, sin colores propios («el
  color que toman depende de mi tema personal de KDE») y con las notificaciones de KDE, no internas. La de este studio:
  1. **El catálogo por disciplina a la izquierda, las curvas en vivo al centro, los parámetros a la derecha** (ya
     estaban) y, **al pie, las verificaciones contra la teoría con su fuente** (`BandaVerificaciones.qml`): cuántas
     pasan y cuándo, la fuente contra la que se verifica (la procedencia que declara el modelo o, si no, su disciplina)
     y una fila por verificación con su resultado en color de estado; en una cita (`Ficha.fuentes`), su propia fuente.
     Va bajo el centro y los parámetros, no bajo el catálogo: es del modelo abierto. Se ve en las vistas del
     experimento (Simulación, Comparación, Sensibilidad); la lista completa sigue en Verificaciones (Ctrl+5) y
     Ctrl+Mayús+T la pliega. Antes las verificaciones eran solo una pestaña: el resultado se leía sin ver contra qué
     se validaba.
  2. **El equilibrio, marcado y dicho**: el punto del gráfico (el acento del tema, como antes) y, sobre él, «Equilibrio
     E» con las cifras de los dos ejes y las de la base. Solo cuando el modelo lo declara (`curvas()["equilibrio"]`): no
     se calcula un cruce que el modelo no afirma.
  3. **Cero colores, radios y tamaños propios**: la pastilla de validez de la cabecera pasa a `EtiquetaNivel` de
     gui-comun; la marca de la base en el deslizador pierde su radio y su ancho en píxeles. Las curvas siguen con los
     roles del tema (`PaletaCategorica.rol`, que conserva el sentido del color del modelo: la demanda azul, la oferta
     roja). La **figura académica** (Ctrl+G, matplotlib, fondo blanco, la paleta del laboratorio) **se conserva fija**:
     es el dato que se exporta al reporte y debe salir igual con cualquier tema, como resolvió Datafw en su §8.19.
  4. **Avisos**: los que no piden decisión ya iban a Plasma por `Mensajes` de la base; las **pistas** ante una acción
     imposible («Elige primero un modelo», por qué no se puede correr o aplicar, que un modelo lento se calcula en un
     hilo aparte) pasan a la barra de estado seis segundos (tipo `pista` en la señal `aviso`). El «NO VÁLIDO» de
     Simulación deja de ser un `InlineMessage`: es un estado, no un aviso, y va en una línea con el color de estado.
  5. **El cambio de claro a oscuro con la ventana abierta**: las fórmulas de la ficha se vuelven a dibujar con el color
     del texto nuevo (antes solo al abrir un modelo). `capturar.py --vivo` lo prueba aislado (`dbus-run-session`, HOME
     y kdeglobals temporales, `notifyChange` solo en ese bus) y detiene por su PID los servicios que ese bus activó.

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
