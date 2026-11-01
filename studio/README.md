---
tipo: readme
estado: activo
---
# studio/ — Simuladores Studio, GUI PySide6 del laboratorio de este repo
<!-- suite:inicio -->
**Suite `simuladores_studio`** · objetivo *publicacion* · estado *activo* · python · interfaz gui

Aplicación de escritorio (PySide6) del laboratorio: los modelos por disciplina con su ficha, ecuaciones, escenarios, verificaciones y el gráfico en vivo.

- Escribe en: ninguno · simula por defecto: no
- Depende de: PySide6, matplotlib, numpy

Comandos:

```bash
main.py
main.py --smoke
main.py --instalar-lanzador [-n]
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-31); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

La ventana del laboratorio con el marco común de los studios (`gui-comun`, acento lima). `sim_app/laboratorio.py`
carga cada disciplina a demanda en su propio espacio de nombres (macro y estadística tienen su `config` y sus `modelos`
con los mismos nombres); `sim_app/ventana.py` arma Inicio y una página por disciplina desde `../catalogo.json`;
`sim_app/pagina_modelo.py` muestra un modelo: ficha, ecuaciones (mathtext), escenarios, verificaciones y el gráfico en
vivo con `graficos._dibujar`.

## Uso

```bash
python3 studio/main.py                       # desde simuladores/
python3 studio/main.py --instalar-lanzador   # el acceso directo del menú (lo hace ../install.sh)
python3 -m pytest -q tests                   # desde simuladores/
```

## Límite honesto

- **Las ecuaciones se dibujan con mathtext**, que no es LaTeX completo: lo que no entiende se muestra como texto.
- **El gráfico es el de las figuras académicas** (fondo blanco) también en el tema oscuro.

