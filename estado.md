---
tipo: estado
estado: activo
actualizado: 2026-11-02
---
# estado.md — simuladores

## Hecho

| fecha | qué | dónde se ve |
|---|---|---|
| 2026-11-02 | Fase 5 dada por buena (el autor delegó la decisión al director con las pruebas en verde y las capturas sobre la muestra): `wip/2026-11-02-qml` fusionada en `main` y retirada; `gui-comun` 2.6.0 (`Grafico`) en `main` y en su remoto con `v2.6.0` | `git log` |
| 2026-11-02 | **Simuladores Studio 2.0, QML + Kirigami sobre `gui-comun` 2.6 (fase 5 de la modernización de la familia)**: espacio de trabajo al estilo Dolphin/Kate (navegación por disciplina y por estado de verificación, tabla de modelos, detalles con Ficha, Escenario generado desde los parámetros, Resultados con el gráfico de QuickCharts (`Grafico`, nuevo en el marco) y las magnitudes frente a la base, Verificaciones con su fuente, Registro, Operación; panel inferior; paleta); F5 corre y lee con el motor, Ctrl+Intro exporta figuras y datos, guarda un escenario propio o regenera el catálogo tras confirmar; `.venv` del repo con matplotlib (`requirements.txt`); laboratorio de muestra para pruebas y capturas; rama `wip/2026-11-02-qml`, sin fusionar hasta el visto bueno del autor | `docs/rediseno.md`; `docs/figuras/simuladores-studio-{oscuro,claro,paleta}.png`; `tests/run.sh` |
| 2026-10-31 | **Simuladores Studio 1.x** (Widgets, `gui-comun` 1.1, acento lima): los 139 modelos por disciplina, su ficha, ecuaciones, escenarios, verificaciones y el gráfico en vivo; retirado el 2026-11-02 por la 2.0 (se lee en la historia de git) | `git log -- studio/sim_app/ventana.py` |
| 2026-10-21 | Adaptador web (fase 3): `navegador.py` y `main.py web` → `navegador.json` (120 de 139 modelos corren en el navegador con Pyodide; fuera, el nivel 12 de macro, que lee datafw, y e26, lento); modelo e67 del TCL (5 verificaciones; las 684 previas, idénticas); `macro/temario.yml` parcial (m10 → macroeconomia-i 3.4); los pilotos IS-LM y TCL corren y redibujan en `web/_aula` | `README.md` §En el navegador · `web/_aula/docs/decisiones.md` §1.20 |
| 2026-10-20 | repo propio fuera de `docencia/simuladores`, con su historia (63 commits por `git subtree split`); `SIMULADORES_DIR` en `core/env`; `main.py catalogo` y `catalogo.json` (138 modelos: 115 de macro, 23 de estadística) | `git log`; etiqueta `antes-simuladores-2026-10-20` en `docencia`, `core` y `divulgacion`; `$RESPALDOS_DIR/renombres/2026-10-20-docencia-simuladores-a-simuladores/` |

## En curso

nada en curso

## Por hacer

- 2026-11-02 · dueño: autor · validar Simuladores Studio 2.0 en la sesión real (Lliphi, Wayland) sobre los modelos de verdad: elegir un modelo, correr un escenario, verificar, Ctrl+G (la figura académica), exportar con Ctrl+Intro, regenerar el catálogo; lo que no convenza se anota aquí y se corrige en `main` o vuelve a `gui-comun`.
- 2026-11-02 · dueño: director · el gráfico en vivo no dibuja las curvas con x no uniforme sino remuestreadas (S6) y las barras con un solo color del acento (el modelo las colorea por semántica: filtraciones/inyecciones); si el autor quiere los colores del modelo, `Grafico` necesitaría una fuente de color por barra desde una paleta del tema.
- 2026-11-02 · dueño: director · `Operación › fuentes` (comprobar las citas) se ofrece en toda disciplina aunque solo estadística tiene el subcomando; macro responde con error de la CLI (código ≠ 0). Ocultarla cuando la disciplina no lo declare.
- 2026-11-02 · dueño: director · el validador (RQ-DOC-11) avisa de `macro/docs/laboratorio-macro.md` (543 líneas, máximo orientativo 300 para una explicación) desde que el repo tiene `docs/`; el documento no cambió desde el 2026-10-20: partirlo o declararlo de otra forma, y refrescar la línea base.
- 2026-11-02 · dueño: director · las citas (`Ficha.fuentes`) solo se comprueban si `core/py-common/biblioteca.py` y Calibre están; fuera del espacio de trabajo quedan «no comprobable» (no cuentan en el estado).
- 2026-10-20 · dueño: director · macro no declara en qué temas de curso vive cada modelo (estadística sí, en `temario.yml`; macro solo m10 desde el 2026-10-21): la vitrina une los recursos `{tipo: simulador}` de los `curso.yml`, pero `catalogo.json` sigue con `cursos: []` en casi todo macro. (m10 ya enlazado en `macroeconomia-i` 3.4 el 2026-10-21.)
- 2026-10-21 · dueño: director · e67 sin `Ficha.fuentes` verificadas (como el resto de estadística; `EXIGIR_FUENTES` sigue en False): citar el TCL contra una edición de Calibre.
- 2026-10-21 · dueño: director · e26 (rango) tarda unos 0,4–0,6 s de CPU por cálculo y queda fuera del navegador: abaratar su simulación si se quiere en la vitrina.
- 2026-10-04 · dueño: campaña SIMULADORES · `macro/modelos/`: tres pendientes sin fecha (aviso A13). Viene de `docencia/estado.md`.
- 2026-10-04 · dueño: campaña SIMULADORES · la excepción de guía anidada de `CLAUDE.md` (docencia, DOC10) se extinguió con el repo propio: cerrar su mención en `DIAGNOSTICO_SIMULADORES_2026-10`. Viene de `docencia/estado.md`.

## Futuro

- Vista ligera precalculada por escenario para celulares lentos (la vista inicial de `navegador.json` ya cubre los valores por defecto).
- Cada modelo declara `curriculo: [{curso, tema}]`, como una pieza de `divulgacion` (web/docs/plataforma-educativa.md §4.8).
