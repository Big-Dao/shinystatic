"""CLI integration tests — shinystatic command line."""

import json
import subprocess
import sys
from pathlib import Path


def _shinystatic(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "shinystatic", *args],
        capture_output=True, text=True, cwd=cwd,
    )


def test_cli_init_writes_templates(tmp_path):
    r = _shinystatic("--init", cwd=tmp_path)
    assert r.returncode == 0
    assert (tmp_path / "typst-preamble.typ").exists()
    assert (tmp_path / "typst-cover.typ").exists()
    content = (tmp_path / "typst-cover.typ").read_text()
    assert "pagebreak" in content


def test_cli_express_generates_py(tmp_path):
    """--mode express generates an executable Python file."""
    qmd = tmp_path / "test.qmd"
    qmd.write_text("""---
title: Test
---
```{python}
#| label: params-defaults
DEFAULTS = {"x": 1}
```
```{python}
#| label: model-reactive
import mylib as mlib
@reactive.calc
def model():
    return mlib.compute()
```
```{python}
#| label: ui-sidebar
with ui.sidebar():
    ui.input_slider("x", "X", 1, 10, 5)
```
""")

    r = _shinystatic("test.qmd", "--mode", "express", cwd=tmp_path)
    assert r.returncode == 0
    out = tmp_path / "test_express.py"
    assert out.exists()
    content = out.read_text()
    assert "from shiny.express import" in content
    assert "with ui.sidebar()" in content


def test_cli_static_generates_qmd(tmp_path):
    """--mode static generates a Quarto document."""
    qmd = tmp_path / "test.qmd"
    qmd.write_text("""---
title: Test
author: T
lang: zh
---
```{python}
#| label: params-defaults
DEFAULTS = {"x": 1}
```
```{python}
#| label: model-reactive
import mylib as mlib
@reactive.calc
def model():
    return mlib.compute(p)
```
```{python}
#| label: text-intro
@render.ui
def text_intro():
    m = model()
    return ui.markdown(f\"\"\"X = {m['x']}\"\"\")
```
""")

    r = _shinystatic("test.qmd", "--mode", "static", cwd=tmp_path)
    assert r.returncode == 0
    out = tmp_path / "test-static.qmd"
    assert out.exists()
    content = out.read_text()
    assert "parameters" in content
    assert "{python}" in content
    assert "mlib.compute" in content


def test_cli_static_with_params_json(tmp_path):
    """--params passes override parameters."""
    qmd = tmp_path / "test.qmd"
    qmd.write_text("""---
title: T
---
```{python}
#| label: params-defaults
DEFAULTS = {"x": 1, "y": 2}
```
```{python}
#| label: model-reactive
import mylib as mlib
@reactive.calc
def model():
    return mlib.compute(p)
```
```{python}
#| label: text-intro
@render.ui
def text_intro():
    m = model()
    return ui.markdown(f\"\"\"X = {m['x']}\"\"\")
```
""")

    params_file = tmp_path / "p.json"
    params_file.write_text(json.dumps({"x": 99, "y": 88}))

    r = _shinystatic("test.qmd", "--mode", "static", "--params", "p.json", cwd=tmp_path)
    assert r.returncode == 0

    # Generated qmd should use override parameter values
    content = (tmp_path / "test-static.qmd").read_text()
    assert "x = 99" in content
    assert "y = 88" in content

    # params.yml should be generated synchronously
    yml = tmp_path / "test-static-params.yml"
    assert yml.exists()


def test_cli_static_output_flag(tmp_path):
    """-o specifies output path."""
    qmd = tmp_path / "test.qmd"
    qmd.write_text("""---
title: T
---
```{python}
#| label: params-defaults
DEFAULTS = {"x": 1}
```
```{python}
#| label: model-reactive
import mylib as mlib
@reactive.calc
def model():
    return mlib.compute(p)
```
""")

    r = _shinystatic("test.qmd", "--mode", "static", "-o", "out.qmd", cwd=tmp_path)
    assert r.returncode == 0
    assert (tmp_path / "out.qmd").exists()


def test_cli_missing_model_graceful(tmp_path):
    """Missing model-* should error without crashing."""
    qmd = tmp_path / "test.qmd"
    qmd.write_text("""---
title: T
---
```{python}
#| label: text-intro
x = 1
```
""")

    r = _shinystatic("test.qmd", "--mode", "static", cwd=tmp_path)
    assert r.returncode != 0
    assert "model-*" in r.stderr


def test_cli_help():
    r = _shinystatic("--help")
    assert r.returncode == 0
    assert "express" in r.stdout
    assert "static" in r.stdout
    assert "--render" in r.stdout
