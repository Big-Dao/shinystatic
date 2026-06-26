"""Shared fixtures."""

from pathlib import Path

import pytest

EXAMPLES = Path(__file__).parent.parent / "examples" / "feasibility"

MINIMAL_QMD = """---
title: "Minimal Test"
subtitle: "For unit testing"
author: "Tester"
date: today
lang: zh
---

# Description

This is a minimal test document.

```{python}
#| label: setup
import numpy as np
import matplotlib.pyplot as plt
```

```{python}
#| label: params-defaults
DEFAULTS = {"x": 10, "y": 20.0, "label": "Test", "items": [1, 2, 3]}
```

```{python}
#| label: model-reactive
import model as mlib

@reactive.calc
def model():
    return mlib.compute({"x": 1, "y": 2})
```

```{python}
#| label: ui-sidebar
with ui.sidebar():
    ui.input_slider("x", "X", 1, 100, 10)
```

```{python}
#| label: text-intro
@render.ui
def text_intro():
    m = model()
    return ui.markdown(f\"\"\"X = {m['x']}, Y = {m['y']:.1f}. Total {m['x'] + m['y']}.\"\"\")
```

```{python}
#| label: fig-test
@render.plot(alt="Test chart")
def fig_test():
    m = model()
    fig, ax = plt.subplots()
    ax.plot([1, 2], [m["x"], m["y"]])
    return fig
```

```{python}
#| label: tbl-test
@render.data_frame
def tbl_test():
    m = model()
    return pd.DataFrame({"A": [m["x"]], "B": [m["y"]]})
```

```{python}
#| label: export-params
@render.ui
def export_params():
    return ui.tags.pre("params")
```
"""


@pytest.fixture(scope="session")
def feasibility_qmd() -> str:
    path = EXAMPLES / "feasibility.qmd"
    if not path.exists():
        pytest.skip("feasibility.qmd does not exist")
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def minimal_qmd() -> str:
    return MINIMAL_QMD
