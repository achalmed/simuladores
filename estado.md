---
tipo: estado
estado: activo
actualizado: 2026-10-20
---
# estado.md — simuladores

## Hecho

| fecha | qué | dónde se ve |
|---|---|---|
| 2026-10-20 | repo propio fuera de `docencia/simuladores`, con su historia (63 commits por `git subtree split`); `SIMULADORES_DIR` en `core/env`; `main.py catalogo` y `catalogo.json` (138 modelos: 115 de macro, 23 de estadística) | `git log`; etiqueta `antes-simuladores-2026-10-20` en `docencia`, `core` y `divulgacion`; `$RESPALDOS_DIR/renombres/2026-10-20-docencia-simuladores-a-simuladores/` |

## En curso

nada en curso

## Por hacer

- 2026-10-20 · dueño: director · macro no declara en qué temas de curso vive cada modelo (estadística sí, en `temario.yml`): sin eso, `catalogo.json` da `cursos: []` en macro. Fuente: los recursos `{tipo: simulador}` de los `curso.yml`.
- 2026-10-04 · dueño: campaña SIMULADORES · `macro/modelos/`: tres pendientes sin fecha (aviso A13). Viene de `docencia/estado.md`.
- 2026-10-04 · dueño: campaña SIMULADORES · la excepción de guía anidada de `CLAUDE.md` (docencia, DOC10) se extinguió con el repo propio: cerrar su mención en `DIAGNOSTICO_SIMULADORES_2026-10`. Viene de `docencia/estado.md`.

## Futuro

- Adaptador web (fase 3 del diseño): el mismo `base.Modelo` en Pyodide, con IS-LM y TCL como piloto y una vista ligera precalculada para el celular.
- Cada modelo declara `curriculo: [{curso, tema}]`, como una pieza de `divulgacion` (web/docs/plataforma-educativa.md §4.8).
