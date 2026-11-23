---
tipo: doc
estado: activo
forma: explicacion
titulo: "La ficha pedagógica de un simulador: resultados de aprendizaje y ejercicios predecir, observar, explicar"
creado: 2026-11-24
---
# La ficha pedagógica de un simulador

Desde el 2026-11-24 (fase 3.3 del plan «aprender y enseñar»). Un simulador que usa un curso ya traía su ficha: la
pregunta, el contexto, los supuestos, las ecuaciones, la intuición, los escenarios con su lectura. Le faltaba lo que
el alumno hace con él: qué debe lograr y con qué ejercicios lo practica. Esa parte es `base.Pedagogia`, dentro de la
misma ficha (`Ficha.pedagogia`), y la valida `pedagogia.py`.

## 1. Qué contiene

| pieza | dónde | qué es |
|---|---|---|
| la pregunta | `Ficha.pregunta` (ya estaba) | la pregunta económica que el simulador ayuda a responder; obligatoria si hay ficha pedagógica |
| los supuestos | `Ficha.supuestos` (ya estaban) | los del modelo, que el alumno lee antes de mover nada; obligatorios si hay ficha pedagógica |
| los resultados | `Pedagogia.resultados: [Resultado(id, nivel, enunciado)]` | lo que el alumno debe lograr, con su nivel de la taxonomía SOLO (`uniestructural`, `multiestructural`, `relacional`, `abstracto_ampliado`), el vocabulario de `docencia/docs/estandar-docencia.md` §10.1; el `id` («r1») es del simulador y el curso lo traduce a su `raN` |
| los ejercicios | `Pedagogia.ejercicios: [Ejercicio(…)]` | el ciclo predecir, mover, observar, explicar y comparar (§2), con la respuesta esperada y el error común para el docente |
| el origen | `Pedagogia.origen` | la forma de `core/py-common/ia_externa.py`: `{autor, herramienta, fecha, verificacion}`; lo que propuso una IA y sigue `pendiente` no sale al alumno (C3.3) |
| lo pendiente | `Pedagogia.pendientes: [str]` | lo que el autor tiene que confirmar; `main.py pedagogia` lo lista como aviso |

Un `Ejercicio` lleva:

| campo | para quién | qué |
|---|---|---|
| `id`, `resultado` | — | «e1», y el `id` del resultado que practica |
| `predecir` | alumno | la pregunta que responde **antes** de mover el control |
| `item` | alumno y aula | si la predicción es cerrada, un ítem del banco de docencia (§10.2: `tipo` `opcion`, `vf` o `numerica`, `enunciado`, `opciones`, `respuesta`, `valor` y `tolerancia`, `errores` por distractor, `bloom`, `dificultad`), sin `id` ni `resultado`, que se toman del ejercicio |
| `escenario` o `cambios` | alumno | qué mover: un escenario del modelo o `{parametro: valor}` dentro del rango del control (uno de los dos) |
| `observar` | alumno | qué mirar en el gráfico o en las cifras (continúa «Observa …») |
| `explicar` | alumno | la pregunta de después: por qué pasó lo que pasó |
| `comparar` | alumno | el contraste con lo predicho; si falta, uno genérico (`pedagogia.COMPARAR`) |
| `respuesta`, `error_comun` | docente | la respuesta esperada (la puesta en común) y el error que el ejercicio anticipa |
| `espera`, `valores` | el validador | la respuesta esperada como aserción: `{magnitud: '↑' \| '↓' \| '='}` frente a la base y `{magnitud: cifra}` tras mover |
| `bloom` | docente | el nivel de Bloom de la explicación (taxonomía revisada, §10.2) |

## 2. El ciclo y por qué tiene esa forma

1. **Predecir** antes de tocar nada. Generar una predicción es una actividad constructiva: produce algo que no estaba
   en el material (Chi y Wylie, 2014, p. 222).
2. **Mover** el control o el escenario. Por sí solo, mover un deslizador o elegir en un menú es apenas activo en ICAP
   (Chi y Wylie, 2014, p. 224): por eso el ejercicio no termina ahí.
3. **Observar** algo dicho de antemano: la curva, el cruce, la cifra. Sin ese foco el alumno mira el gráfico como una
   demostración, que es lo que el aprendizaje activo sustituye (Freeman et al., 2014, p. 8413).
4. **Explicar** por escrito por qué pasó lo que pasó: otra vez constructivo, y la pieza que pide el resultado
   relacional.
5. **Comparar** con lo predicho. Si no coincide, el alumno busca qué paso de su razonamiento falló. Discutirlo en
   parejas en la puesta en común es el modo interactivo, el de mayor efecto (Chi y Wylie, 2014, p. 235, sobre
   Deslauriers et al., 2011).

Cada ejercicio declara el **error común** que anticipa, y cada distractor de una predicción cerrada, el suyo: los
instrumentos que más miden el efecto del aprendizaje activo son los que diagnostican concepciones erróneas conocidas
(Freeman et al., 2014, p. 8411), y la retroalimentación por distractor del aula (plan, fase 5.1) las necesita escritas.
Que el ciclo sea predecir, observar y explicar viene de White y Gunstone (1992), y que la simulación vaya **guiada**,
no como descubrimiento libre, de de Jong y van Joolingen (1998), Mayer (2004) y Alfieri et al. (2011): esas cuatro
obras no están en Calibre (§5).

Por eso un ejercicio da **dos ítems** al banco de docencia: la predicción, cerrada, que el aula corrige sola y
retroalimenta por distractor (`m04-e1-predecir`), y la explicación, abierta, para la puesta en común, con la respuesta
esperada y el error común (`m04-e1-explicar`).

## 3. La clave no puede contradecir al simulador

La respuesta esperada de cada ejercicio se dice también como aserción (`espera`, `valores`) y `pedagogia.comprobar`
corre el modelo con lo que el ejercicio manda mover: si el modelo da otra dirección u otra cifra (tolerancia relativa de
0,5 %), es un error. `base.verificar` agrega a cada modelo con ficha pedagógica una verificación más, «ficha pedagógica
(resultados y ejercicios)», así que `main.py verificar`, el studio y la matriz la cuentan como cualquier otra: un
ejercicio con la clave equivocada deja el modelo en rojo.

`pedagogia.problemas` además rechaza: un nivel fuera de SOLO o de Bloom; un ejercicio sin `predecir`, `explicar`,
`respuesta` o `error_comun`; un resultado que no existe; un escenario que no existe, un parámetro que no existe o un
valor fuera del rango del control (el alumno no podría moverlo ahí); un ejercicio sin `espera` ni `valores`; un ítem
que no cumple §10.2 (la misma regla que `alineamiento.problemas_item`, que la prueba compara con la de docencia); y un
`origen` de IA sin herramienta. Avisa: un resultado que ningún ejercicio practica, lo propuesto por la IA sin verificar,
la cifra de un ítem numérico que no está entre los `valores`, y cada pendiente del autor.

## 4. Quién lo lee

| quién | qué recibe | cómo |
|---|---|---|
| el docente, en Simuladores Studio | la ficha con «Resultados de aprendizaje» y «Ejercicios», con las claves | `fichas.markdown(…, pedagogia=)`, que el controlador pide a `pedagogia.markdown(docente=True, completo=False)` del laboratorio activo |
| el docente, en el reporte | la misma sección en `salidas/…/reporte.md` | `reporte.py` |
| el alumno, impreso o en el aula virtual | la hoja sin claves | `python3 main.py pedagogia macro/m04 --formato alumno` (`--formato docente`, la guía con claves) |
| `docencia` (banco de recuperación) | los ítems en el esquema §10.2, en YAML | `python3 main.py pedagogia macro/m04 --formato banco`: se pegan en `preguntas:` de un `recuperacion.yml` y su `resultado` («r1») se cambia por el `raN` del curso; desde ahí `alineamiento.py exportar` los lleva al aula, a la API y a `academic-exam` como a cualquier otro ítem |
| los pubs y el aula (`catalogo.json`, `navegador.json`) | `ficha.pedagogia`: resultados y ejercicios **sin** respuesta, valores, errores ni origen | solo si `origen.verificacion` es `verificada` (o el autor es persona); por eso hoy ninguno de los dos JSON lleva fichas pedagógicas, y el único cambio es `esquema: 2` |

Lo propuesto por la IA queda fuera de todo lo que llega al alumno hasta que el docente lo verifica: no sale en los dos
JSON y, en docencia, `alineamiento.py` no lo exporta mientras su `origen.verificacion` sea `pendiente` (estándar §10.2).
Para verificar una ficha: leerla con `--formato docente`, corregir lo que haga falta en el modelo y cambiar
`verificacion: "pendiente"` por `"verificada"` en su `origen`; después, `main.py catalogo --aplicar` y
`main.py web --aplicar`.

## 5. Sustento

Las citas que están en Calibre son también aserciones: `pedagogia.FUNDAMENTO` las guarda como `base.Fuente` y la
prueba `test_el_fundamento_se_comprueba_contra_calibre` comprueba cada pasaje en su hoja con `fuentes.py`.

| obra | página (hoja del PDF) | pasaje leído | qué funda |
|---|---|---|---|
| Freeman et al. (2014), Calibre 11175 | 8413 (4) | «Active learning engages students in the process of learning through» | el simulador se usa con una tarea del alumno |
| Freeman et al. (2014), 11175 | 8410 (1) | «students in classes with traditional lecturing were 1.5 times more» [likely to fail] | el ejercicio reemplaza la exposición del modelo, no la adorna |
| Freeman et al. (2014), 11175 | 8411 (2) | «diagnose known misconceptions, in contrast to course examinations» | cada ejercicio y cada distractor declaran su error común |
| Chi y Wylie (2014), 11161 | 222 (5) | «generate or produce additional externalized outputs or» [products] | predecir y explicar por escrito: modo constructivo |
| Chi y Wylie (2014), 11161 | 222 (5) | «generating predictions (Schauble, Glaser, Duschl,» | la predicción previa es constructiva |
| Chi y Wylie (2014), 11161 | 224 (7) | «selecting is only active in our taxonomy» | mover un control o elegir una opción no basta: se pide explicar |
| Chi y Wylie (2014), 11161 | 235 (18) | «(passive) to an intervention consisting of predicting» | la puesta en común en parejas: modo interactivo |
| Eberly Center (s. f.), 10516 | s. p. (1) | «The updated version by Anderson and Krathwohl (2001)» | el nivel de Bloom del ítem (el mismo apoyo que usa docencia §10.2) |

**Pendientes** (no están en Calibre, o están sin archivo; se ingresan por `biblioteca-studio`, `lib/ingresar.py`). Los
DOI se cotejaron en Crossref el 2026-11-24 (título, revista, año, volumen y páginas).

- White, R. T. y Gunstone, R. F. (1992). *Probing understanding*. Falmer Press. Motivo: el ciclo predecir, observar,
  explicar (cap. «Prediction-observation-explanation»); no está en Calibre.
- de Jong, T. y van Joolingen, W. R. (1998). Scientific discovery learning with computer simulations of conceptual
  domains. *Review of Educational Research, 68*(2), 179–201. https://doi.org/10.3102/00346543068002179. Motivo: el
  aprendizaje con simulaciones y por qué necesita guía; no está en Calibre.
- Mayer, R. E. (2004). Should there be a three-strikes rule against pure discovery learning? The case for guided methods
  of instruction. *American Psychologist, 59*(1), 14–19. https://doi.org/10.1037/0003-066X.59.1.14. Motivo:
  descubrimiento guiado frente a libre; no está en Calibre.
- Alfieri, L., Brooks, P. J., Aldrich, N. J. y Tenenbaum, H. R. (2011). Does discovery-based instruction enhance
  learning? *Journal of Educational Psychology, 103*(1), 1–18. https://doi.org/10.1037/a0021017. Motivo: el metaanálisis
  del descubrimiento guiado; no está en Calibre.
- Crouch, C. H., Fagen, A. P., Callan, J. P. y Mazur, E. (2004). Classroom demonstrations: Learning tools or
  entertainment? *American Journal of Physics, 72*(6), 835–838. https://doi.org/10.1119/1.1707018. Motivo: predecir
  antes de ver una demostración (lo más cercano a mover un simulador en clase); no está en Calibre.
- Deslauriers, L., Schelew, E. y Wieman, C. (2011). Improved learning in a large-enrollment physics class. *Science,
  332*(6031), 862–864. https://doi.org/10.1126/science.1201783. Motivo: se cita a través de Chi y Wylie (2014, p. 235);
  leer la obra misma.
- Biggs, J. B. y Collis, K. F. (1982). *Evaluating the quality of learning: The SOLO taxonomy (Structure of the Observed
  Learning Outcome)*. Academic Press. Motivo: los niveles SOLO de los resultados; en Calibre solo están Biggs (1996,
  11150) y Biggs, Tang y Kennedy (2022, 11151), ambos sin archivo, como los cita docencia §10.1.
- Butler, A. C. y Roediger, H. L. (2008). Feedback enhances the positive effects and reduces the negative effects of
  multiple-choice testing. *Memory & Cognition, 36*(3), 604–616. https://doi.org/10.3758/MC.36.3.604. Motivo: la
  retroalimentación por distractor; pendiente también en docencia.
- Allgood, S., Walstad, W. B. y Siegfried, J. J. (2015). Research on teaching economics to undergraduates. *Journal of
  Economic Literature, 53*(2), 285–325. https://doi.org/10.1257/jel.53.2.285. Calibre 11139 (el DOI es el de su
  registro), sin archivo. Motivo: la evidencia propia de la enseñanza de la economía; por leer.

## 6. Los simuladores con ficha pedagógica

Los tres que enlaza `macroeconomia-i` (los de `econometria-i` no enlazan simuladores): m04 (tema 3.2, multiplicador),
m10 (3.4, IS-LM) y m20 (3.1, la AD derivada del IS-LM), con dos resultados y tres ejercicios cada uno, y cada clave
comprobada contra el modelo. Los escribió la IA desde el código de cada modelo y quedan `verificacion: pendiente`; sus
pendientes (el nivel SOLO por confirmar, el paso de «r1» a los `raN` del curso, los artefactos lineales de m10 y m20 en
los extremos, la apertura de m20 con `dG = 50`) los lista `python3 main.py pedagogia`.

## 7. Límites

- El vocabulario (SOLO, Bloom, tipos, dificultad) es una copia del de `docencia/scripts/alineamiento.py`: el motor no
  lee otros repos. La prueba `test_la_regla_del_item_es_la_de_docencia` los compara cuando docencia está al lado.
- El simulador no conoce los resultados del curso: el `resultado` de un ítem es del simulador hasta que alguien lo
  traduce al `raN` del curso al pegarlo en su banco.
- La comprobación cubre las direcciones y las cifras de `resultados()`; lo que el alumno debe mirar en el gráfico (una
  pendiente, una curva que deja de ser paralela) lo sostiene la ecuación del modelo y sus verificaciones, no esta
  comprobación.
