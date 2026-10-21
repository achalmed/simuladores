---
tipo: estado
estado: activo
actualizado: 2026-10-21
---
# estado.md — simuladores

## Hecho

| fecha | qué | dónde se ve |
|---|---|---|
| 2026-10-21 | Adaptador web (fase 3): `navegador.py` y `main.py web` → `navegador.json` (120 de 139 modelos corren en el navegador con Pyodide; fuera, el nivel 12 de macro, que lee datafw, y e26, lento); modelo e67 del TCL (5 verificaciones; las 684 previas, idénticas); `macro/temario.yml` parcial (m10 → macroeconomia-i 3.4); los pilotos IS-LM y TCL corren y redibujan en `web/_aula` | `README.md` §En el navegador · `web/_aula/docs/decisiones.md` §1.20 |
| 2026-10-20 | repo propio fuera de `docencia/simuladores`, con su historia (63 commits por `git subtree split`); `SIMULADORES_DIR` en `core/env`; `main.py catalogo` y `catalogo.json` (138 modelos: 115 de macro, 23 de estadística) | `git log`; etiqueta `antes-simuladores-2026-10-20` en `docencia`, `core` y `divulgacion`; `$RESPALDOS_DIR/renombres/2026-10-20-docencia-simuladores-a-simuladores/` |

## En curso

nada en curso

## Por hacer

- 2026-10-20 · dueño: director · macro no declara en qué temas de curso vive cada modelo (estadística sí, en `temario.yml`; macro solo m10 desde el 2026-10-21): la vitrina une los recursos `{tipo: simulador}` de los `curso.yml`, pero `catalogo.json` sigue con `cursos: []` en casi todo macro. Que docencia enlace m10 en `macroeconomia-i` 3.4 (`enlazar.py simuladores`).
- 2026-10-21 · dueño: director · e67 sin `Ficha.fuentes` verificadas (como el resto de estadística; `EXIGIR_FUENTES` sigue en False): citar el TCL contra una edición de Calibre.
- 2026-10-21 · dueño: director · e26 (rango) tarda unos 0,4–0,6 s de CPU por cálculo y queda fuera del navegador: abaratar su simulación si se quiere en la vitrina.
- 2026-10-04 · dueño: campaña SIMULADORES · `macro/modelos/`: tres pendientes sin fecha (aviso A13). Viene de `docencia/estado.md`.
- 2026-10-04 · dueño: campaña SIMULADORES · la excepción de guía anidada de `CLAUDE.md` (docencia, DOC10) se extinguió con el repo propio: cerrar su mención en `DIAGNOSTICO_SIMULADORES_2026-10`. Viene de `docencia/estado.md`.

## Futuro

- Vista ligera precalculada por escenario para celulares lentos (la vista inicial de `navegador.json` ya cubre los valores por defecto).
- Cada modelo declara `curriculo: [{curso, tema}]`, como una pieza de `divulgacion` (web/docs/plataforma-educativa.md §4.8).
