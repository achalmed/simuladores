---
tipo: guia_ia
estado: activo
---
# CLAUDE.md — simuladores (el laboratorio computacional)

Guía para el asistente en este repo; solo dice lo que el `CLAUDE.md` raíz no dice. `AGENTS.md` es un enlace a este
archivo. Léase antes: `README.md` (uso, estructura, consumidores) y `estado.md`.

Laboratorio pedagógico multi-disciplina, **repo propio desde el 2026-10-20** (`SIMULADORES_DIR` de `core/env.py`; antes
`docencia/simuladores` y antes `datafw/simuladores`, con la historia conservada). Es **currículo** —fichas pedagógicas,
verificaciones que son teoremas, animaciones— y lo consumen `docencia` (recursos `{tipo: simulador}` de `curso.yml`,
enlazados por `docencia/scripts/enlazar.py simuladores`), `divulgacion` (`divulgacion/lib/simuladores.py` importa el modelo) y,
desde la fase 4 de la plataforma educativa, los pubs (`catalogo.json`).

## Reglas del repo

- **La interfaz de `base.Modelo` es contrato**: `curvas`, `parametros`, `escenarios`, `verificaciones`,
  `ecuaciones_calibradas` y `ficha` los usa `divulgacion` directamente. No se renombran ni cambian de forma sin migrar
  antes a ese consumidor.
- **`catalogo.json` es GENERADO** (`python3 main.py catalogo --aplicar`) y es el contrato de los pubs: tras añadir o
  cambiar un modelo se regenera, y `main.py catalogo --verificar` debe dar 0. Si cambia un campo, sube `ESQUEMA` en
  `main.py`. Igual **`navegador.json`** (`main.py web --aplicar`, para Pyodide: solo numpy, stdlib, `modelos.*`).
- **Cada disciplina declara su `AREA`** en su `config.py` con el vocabulario cerrado de `docencia/config/areas.yml`
  (decide el pub que publica sus modelos); nunca en el motor.
- **Nada de rutas a otros repos**: `core/` se localiza subiendo carpetas (`_datos_bcrp.py`, `fuentes.py`) y desde ahí
  `DATAFW_DIR` y la biblioteca; ningún `docencia/…` ni `../` hacia fuera.

## Estructura: un laboratorio, varias disciplinas hermanas

El MOTOR compartido (agnóstico a la disciplina) vive en la RAÍZ: `base.py` (dataclasses, cálculo, verificación; SIN
matplotlib), `graficos.py` (render matplotlib: colocación automática de etiquetas anti-solape, dibujo progresivo),
`laboratorio.py` (láminas de experimento), `app.py` (LA aplicación: `python3 main.py` sin argumentos abre el recorrido
pedagógico progresivo; los subcomandos CLI son herramientas técnicas) y `reporte.py` (MD). Cada disciplina es una
subcarpeta con su propio `config.py`/`main.py`/`modelos/`: `macro/` (completa), `estadistica/` (en curso), y futuras
`econometria/`/`micro/`/`mate/`. El `main.py` de cada disciplina añade la raíz al `sys.path` (motor) y su carpeta
primero (su `config` y `modelos` ganan): así se comparte el motor sin copiarlo. Correr: `cd <disciplina> && python3
main.py …`. Los `docs/`, `salidas/` (regenerables, no se versionan) y la `matriz_trazabilidad.csv` de cada disciplina
viven en su subcarpeta. Código común de un nivel va en `modelos/nivel_NN/_*.py` (el guion bajo lo excluye del
descubrimiento).

## Reglas de un modelo

Un modelo = un archivo `modelos/nivel_NN/<id>_slug.py` con `Ficha` pedagógica completa (contexto histórico, autores,
supuestos, ecuaciones explicadas, intuición, limitaciones, evolución; derivación LaTeX en estadística), `escenarios`
con lectura y `verificaciones` numéricas (identidades exactas, convergencias con tolerancia; en estadística, los
TEOREMAS: $E[\bar X]=\mu$, TCL…). Plantilla académica de 20 puntos en §2 del diseño de macro: modelos nuevos traen
`pregunta`, `cadena` de transmisión por escenario y, cuando aplique,
`derivacion`/`variables`/`ecuaciones_calibradas`/`grupo`. Reglas duras: procedencia declarada (sin citas de página no
verificadas; regla 00a de datafw): en estadística, `Ficha.fuentes` con `base.Fuente(calibre_id, pagina, pagina_pdf,
pasaje)` que `fuentes.py` comprueba contra la hoja del PDF (`main.py fuentes`); la procedencia por defecto es de cada
disciplina (`config.PROCEDENCIA_POR_DEFECTO`), nunca del motor; calibraciones didácticas ≠ datos oficiales; `python3
main.py verificar` al 100 % y fila en la `matriz_trazabilidad.csv` de su disciplina antes de dar un modelo por bueno;
aleatoriedad con `np.random.default_rng(semilla)`. Figuras con tipografía académica (mathtext STIX, notación `$…$` en
ejes y leyendas; opción `USAR_TEX_COMPLETO` en config). Cada concepto se DERIVA, SIMULA y VISUALIZA: no es una fórmula
(regresión = derivar $\hat\beta=(X'X)^{-1}X'Y$, no llamar `lm()`).

## Macroeconomía (`macro/`)

Currículo completo por niveles (recuento: `cd macro && python3 main.py verificar`); plan vigente en
`macro/docs/laboratorio-macro.md`. El nivel 12 es el laboratorio del Perú con datos reales del BCRP: m97-m115 usan
series macro (PBI, IPC, tasa, tipo de cambio, cobre, términos de intercambio, bloque fiscal) que descarga
`datafw/connectors/bcrp`; el detalle mensual se lee de `datafw/data/raw/bcrp/<categoría>/` **por nombre**, con el
lector único de `datafw/metodos/series/lectores.py` cuando está (`macro/modelos/nivel_12/_datos_bcrp.py` localiza
`core/env.py: DATAFW_DIR`) y, si no está, cae al snapshot anual embebido en `_series_bcrp.py` (auto-contenido).
Verifica contra el dato real, no contra calibración didáctica: coef. Taylor 0,55 < 1 = sesgo de variable omitida
(m100); correlación tasa-inflación = causalidad inversa (m101); canal del cobre (m103-m105: TdI mueven el INGRESO, no
el PBI-volumen); inversión pública corr ≈ 0 porque es contracíclica (m106-m108) vs exportaciones exógenas (m109);
shock externo real y financiero (m110-m111); enclave minero (m112); passthrough ≈ 0 (m113); El Niño como shock de
oferta (m114); síntesis (m115). Tras macro vendrán micro/econometría/mate (§9 del diseño); la econometría pedagógica
NO duplicará `datafw/pipeline/`.

## Estadística (`estadistica/`)

Currículo por secciones (fundamentos → aprendizaje automático); diseño en
`estadistica/docs/laboratorio-estadistica.md`; mapa de temas (id, estado, temas de `curso.yml`) en
`estadistica/temario.yml`: los números que ya citan los modelos son anclas, no se renumeran. Estado: `cd estadistica
&& python3 main.py verificar`; plan de cierre en
`meta/docs/historial/diagnosticos/DIAGNOSTICO_SIMULADORES_2026-10.md`; la app interactiva es la del motor (`app.py`) y
ya sirve a esta disciplina. DOS renderizadores, un modelo: matplotlib (app + reportes) y **Manim**
(`estadistica/animaciones/`, «ver el método en movimiento»), que corre en un env conda APARTE (`manim-datafw`, Manim
0.20.1 sobre ffmpeg + TeX Live) porque `manimpango` no tiene wheel para py3.13; utilidades comunes en `_comun.py`
(prohibido copiarlas).

## Relación con el resto del ecosistema

- Datos reales: de `datafw` por nombre (`core/env.py`), nunca por rutas relativas ni copias; aquí no se adquieren.
- Cursos: `curso.yml` enlaza `{tipo: simulador, archivo: simuladores/<disciplina>/modelos/…}` (`enlazar.py simuladores`
  propone, `enlazar.py verificar` comprueba y, durante la migración, traduce los `docencia/simuladores/…`).

## Cómo se verifica un cambio

```bash
cd ~/Documents/simuladores
python3 main.py verificar && python3 main.py catalogo --verificar && python3 main.py web --verificar   # al 100 % y contratos al día
python3 -m py_compile *.py */main.py */config.py
cd ~/Documents && python3 core/archivos.py validar simuladores --linea-base "$LINEA_BASE_VALIDADOR"
cd ~/Documents/divulgacion && python3 main.py doctor   # «simuladores (N modelos en uso)» en verde
```
