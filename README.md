---
tipo: readme
estado: activo
---
# simuladores/ — el laboratorio computacional (multi-disciplina)

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

## Límite honesto

- Es un laboratorio pedagógico: los modelos reproducen teoremas y escenarios de manual, no pronósticos. Los que usan
  datos reales (el nivel 12 de macro, con series del BCRP) los leen de `datafw` por nombre; el laboratorio no adquiere datos.
- «Página verificada» significa que el pasaje citado está en esa hoja del PDF del `calibre_id`: lo comprueba
  `fuentes.py` con el texto que da `core/py-common/biblioteca.py`. Sin la biblioteca en la máquina, la cita queda
  «no comprobable», no verificada; y la página impresa solo se confirma si el PDF trae el folio en su texto.
- `catalogo.json` describe los modelos, no los ejecuta: las cifras de un escenario se calculan con el modelo. Los
  `cursos` del catálogo salen del `temario.yml` de cada disciplina (hoy solo estadística); macro aún no declara los suyos.
- Sin remoto: publicar el repo es decisión del autor.
