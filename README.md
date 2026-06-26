# shinystatic

[![CI](https://github.com/Big-Dao/shinystatic/actions/workflows/ci.yml/badge.svg)](https://github.com/Big-Dao/shinystatic/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](https://github.com/Big-Dao/shinystatic)
[![Mypy](https://img.shields.io/badge/mypy-strict-blue)](https://github.com/Big-Dao/shinystatic)

Convert **Shiny Express `.qmd`** documents to:
- **Static `.qmd`** — render with Quarto + Typst for professional PDF output
- **Standalone Express app** — debug interactively with `shiny run`

## Install

```bash
pip install shinystatic
# or
uv add shinystatic
```

## Quick Start

```bash
# 1. Write Typst templates
shinystatic --init

# 2. Interactive debugging
shinystatic doc.qmd --mode express
shiny run doc_express.py

# 3. Generate PDF
shinystatic doc.qmd --mode static --render
```

## Source Conventions

| Label Prefix | Purpose |
|-------------|---------|
| `setup` | Imports & matplotlib config |
| `params-*` | DEFAULTS dict (parameter definitions) |
| `model-*` | `@reactive.calc` model function |
| `ui-*` | Shiny sidebar / UI widgets (removed in PDF) |
| `text-*` | `@render.ui` body text → `{python}` inline |
| `fig-*` | `@render.plot` figures → `plt.show()` |
| `tbl-*` | `@render.data_frame` tables |
| `export-*` | Export/download buttons (removed in PDF) |

## Example

See [`examples/feasibility/`](examples/feasibility/) — a heavy/medium truck supercharger station feasibility analysis.

```bash
cd examples/feasibility
uv pip install --python ../../.venv/bin/python pyyaml jupyter numpy pandas matplotlib
PATH=../../.venv/bin:$PATH quarto check jupyter
shinystatic feasibility.qmd --mode static --render
```

If Quarto reports `No module named 'yaml'` or `Jupyter is not available`, it is using a Python interpreter without required runtime packages.
Run Quarto with the same virtual environment used by this project (as shown above with `PATH=../../.venv/bin:$PATH`).

## License

MIT
