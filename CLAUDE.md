# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`shinystatic` — a CLI tool that converts **Shiny Express `.qmd`** files into static Quarto documents (for Typst PDF rendering) or standalone Express apps (for interactive debugging). Zero runtime dependencies beyond Python stdlib; templates are embedded as strings in `core.py`.

## Commands

```bash
uv sync                                          # install dependencies
mypy src/shinystatic --strict                    # type check
python -m pytest tests/ -q --cov=shinystatic --cov-fail-under=90  # full suite
python -m pytest tests/test_core.py -q           # single file
python -m pytest tests/test_core.py::test_name -q  # single test
shinystatic --init                               # write Typst templates locally
shinystatic doc.qmd --mode express               # generate standalone Express app
shinystatic doc.qmd --mode static --render       # convert + render PDF
```

## Architecture

**Core pipeline** (`src/shinystatic/core.py`, ~255 lines): `convert_static()` reads a `.qmd` source, parses cells by `#| label:`, and dispatches each cell to a type-specific converter. The key insight: the static output keeps `m['key']` dictionary access as-is in `{python}` inline expressions — no variable name mapping needed.

**Cell label convention** (the contract between source `.qmd` and converter):

| Prefix | Converter action |
|--------|-----------------|
| `setup` | Extract non-Shiny imports → `setup-static` cell |
| `params-*` | Parse `DEFAULTS = {...}` → Papermill `parameters` cell |
| `model-*` | Detect `import X as Y` / `return Y.func()` → `model-static` cell calling `Y.func(_params)` |
| `text-*` | Extract `ui.markdown(f"""...""")`, expand locals, convert `{expr}` → `{python} expr` inline |
| `fig-*` | Remove `@render.plot`, replace `model()` → `m`, add `plt.show()` |
| `tbl-*` | Remove `@render.data_frame`, `model()` → `m`, strip `return` |
| `ui-*` / `export-*` | Delete cell and surrounding markdown section |

**`convert_text_cell` specifics**: Local variables defined before `return` (e.g., `total = m['a'] + m['b']`) are inlined into the f-string body before conversion. Format-spec expressions (`{expr:fmt}`) are wrapped in `f"{...}"` to preserve the specifier. Without a format spec, the raw expression is used directly.

**`generate_express()`** assembles a standalone Shiny Express `.py` app from the same cells (excluding `setup` which is replaced by a header template).

**Tests** live in `tests/`: `test_core.py` (unit + integration), `test_text.py` (text converter all branches), `test_snapshot.py` (4 regression snapshots), `test_cli.py` (subprocess CLI). Snapshots require regeneration after any output-affecting change: `rm -rf tests/snapshots && pytest tests/test_snapshot.py --snapshot-update`.

**Example** at `examples/feasibility/`: a heavy/medium truck supercharger station feasibility report, with `model.py` (shared computation), `feasibility.qmd` (Shiny Express source), and `params.yml` (sample overrides).

## Key rules

- `pyproject.toml` `addopts` has `--cov-fail-under=90` — any test run from CLI enforces the coverage gate
- CI (`.github/workflows/ci.yml`) runs pytest + mypy on Python 3.10 and 3.13
- `uv.lock` is committed (this is an application, not a library)
- `.pre-commit-config.yaml` runs ruff + mypy pre-commit (no pytest hook — too slow)
