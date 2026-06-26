"""Unit tests for shinystatic.core."""

import re

from shinystatic.core import (
    build_static_yaml,
    convert_fig_cell,
    convert_static,
    convert_tbl_cell,
    detect_model_module,
    extract_defaults,
    generate_express,
    generate_parameters_cell,
    parse_cells,
    parse_yaml,
)


# ════════════════════════════════════
# parse_yaml
# ════════════════════════════════════

def test_parse_yaml_extracts_metadata(minimal_qmd):
    meta, _ = parse_yaml(minimal_qmd)
    assert meta["title"] == "Minimal Test"
    assert meta["author"] == "Tester"
    assert meta["lang"] == "zh"


def test_parse_yaml_returns_body(minimal_qmd):
    _, body = parse_yaml(minimal_qmd)
    assert "# Description" in body
    assert "---" not in body[:50]  # YAML stripped


def test_parse_yaml_no_yaml():
    meta, body = parse_yaml("# Body only\nNo YAML")
    assert meta == {}
    assert "Body only" in body


# ════════════════════════════════════
# build_static_yaml
# ════════════════════════════════════

def test_build_static_yaml_includes_metadata():
    yaml = build_static_yaml({"title": "T", "subtitle": "S", "author": "A", "date": "today", "lang": "zh"})
    assert 'title: "T"' in yaml
    assert 'subtitle: "S"' in yaml
    assert 'author: "A"' in yaml
    assert "typst:" in yaml
    assert "typst-preamble.typ" in yaml
    assert "typst-cover.typ" in yaml


def test_build_static_yaml_no_shiny():
    yaml = build_static_yaml({"title": "X"})
    assert "shiny" not in yaml
    assert "typst" in yaml


# ════════════════════════════════════
# parse_cells
# ════════════════════════════════════

def test_parse_cells_finds_labels(minimal_qmd):
    _, body = parse_yaml(minimal_qmd)
    cells = parse_cells(body)
    labels = [c["label"] for c in cells if c["type"] == "python" and c["label"]]
    assert "setup" in labels
    assert "params-defaults" in labels
    assert "model-reactive" in labels
    assert "ui-sidebar" in labels
    assert "text-intro" in labels
    assert "fig-test" in labels
    assert "tbl-test" in labels
    assert "export-params" in labels


def test_parse_cells_markdown_preserved(minimal_qmd):
    _, body = parse_yaml(minimal_qmd)
    cells = parse_cells(body)
    md_texts = [c["code"] for c in cells if c["type"] == "markdown"]
    combined = "".join(md_texts)
    assert "minimal test document" in combined


# ════════════════════════════════════
# extract_defaults
# ════════════════════════════════════

def test_extract_defaults_from_params(minimal_qmd):
    _, body = parse_yaml(minimal_qmd)
    cells = parse_cells(body)
    d = extract_defaults(cells)
    assert d["x"] == 10
    assert d["y"] == 20.0
    assert d["label"] == "Test"
    assert d["items"] == [1, 2, 3]


def test_extract_defaults_from_feasibility(feasibility_qmd):
    _, body = parse_yaml(feasibility_qmd)
    cells = parse_cells(body)
    d = extract_defaults(cells)
    assert "n_heavy" in d
    assert "service_fee" in d
    assert isinstance(d["n_heavy"], int)


# ════════════════════════════════════
# generate_parameters_cell
# ════════════════════════════════════

def test_generate_parameters_cell():
    defaults = {"a": 1, "b": 2.0, "c": "hello", "d": [1, 2]}
    result = generate_parameters_cell(defaults)
    assert "#| tags: [parameters]" in result
    assert "a = 1" in result
    assert "b = 2.0" in result
    assert 'c = "hello"' in result
    assert "d = [1, 2]" in result


# ════════════════════════════════════
# detect_model_module
# ════════════════════════════════════

def test_detect_import_as(feasibility_qmd):
    """Detect 'import model as mlib' pattern."""
    _, body = parse_yaml(feasibility_qmd)
    cells = parse_cells(body)
    result = detect_model_module(cells)
    assert result == ("mlib", "compute")


def test_detect_from_import_as():
    """Detect 'from X import Y as Z' pattern."""
    cells = [{
        "type": "python", "label": "model-reactive",
        "code": "from relay.model import compute as cmp\nreturn cmp.run(p)",
    }]
    result = detect_model_module(cells)
    assert result == ("cmp", "run")


def test_detect_returns_none_when_no_model():
    cells = [{"type": "python", "label": "text-intro", "code": "x = 1"}]
    assert detect_model_module(cells) is None


# ════════════════════════════════════
# convert_fig_cell
# ════════════════════════════════════

FIG_CODE = """@render.plot(alt="Test")
def fig_test():
    m = model()
    fig, ax = plt.subplots()
    ax.plot([1, 2], [m["x"], m["y"]])
    return mlib.plot_revenue(model())
"""


def test_convert_fig_replaces_model_calls():
    result = convert_fig_cell(FIG_CODE)
    assert "model()" not in result
    assert "mlib.plot_revenue(m)" in result


def test_convert_fig_adds_plt_show():
    result = convert_fig_cell(FIG_CODE)
    assert "plt.show()" in result


def test_convert_fig_removes_render_decorator():
    result = convert_fig_cell(FIG_CODE)
    assert "@render.plot" not in result
    assert "def fig_test" not in result


# ════════════════════════════════════
# convert_tbl_cell
# ════════════════════════════════════

TBL_CODE = """@render.data_frame
def tbl_test():
    m = model()
    df = pd.DataFrame({"A": [m["x"]]})
    return df
"""


def test_convert_tbl_removes_render():
    result = convert_tbl_cell(TBL_CODE)
    assert "@render.data_frame" not in result
    assert "def tbl_test" not in result


def test_convert_tbl_replaces_model():
    result = convert_tbl_cell(TBL_CODE)
    assert "model()" not in result
    assert "m" in result


def test_convert_tbl_removes_return():
    result = convert_tbl_cell(TBL_CODE)
    assert "return df" not in result
    assert "df" in result


# ════════════════════════════════════
# convert_static — Integration tests
# ════════════════════════════════════

def test_convert_static_with_feasibility(feasibility_qmd):
    result, meta = convert_static(feasibility_qmd)
    assert meta["title"] == "Heavy/Medium-Duty Truck Supercharging Station Feasibility Analysis"
    assert "parameters" in result
    assert "model-static" in result
    assert "setup-static" in result
    assert "{python}" in result
    assert "shiny" not in result  
    assert "@render" not in result  
    assert "ui-sidebar" not in result  
    assert "export-" not in result  


def test_convert_static_no_model_calls(feasibility_qmd):
    result, _ = convert_static(feasibility_qmd)
    # model() calls should be replaced with m
    assert "model()" not in result


# ════════════════════════════════════
# generate_express
# ════════════════════════════════════

def test_generate_express_output(feasibility_qmd):
    result = generate_express(feasibility_qmd)
    assert "from shiny.express import input, render, ui" in result
    assert "with ui.sidebar()" in result
    assert "@render.ui" in result
    assert "@render.plot" in result
    assert "import model as mlib" in result


def test_generate_express_no_yaml(feasibility_qmd):
    result = generate_express(feasibility_qmd)
    assert "---" not in result


# ════════════════════════════════════
# Edge cases
# ════════════════════════════════════

def test_parse_cells_empty():
    cells = parse_cells("")
    assert cells == []


def test_parse_cells_no_python():
    cells = parse_cells("# Markdown only\n\nNo code blocks.")
    assert len(cells) == 1
    assert cells[0]["type"] == "markdown"


def test_extract_defaults_no_defaults():
    cells = [{"type": "python", "label": "text-intro", "code": "x = 1"}]
    assert extract_defaults(cells) == {}


def test_convert_static_raises_without_model():
    bad_qmd = "---\ntitle: X\n---\n\n```{python}\n#| label: text-intro\nx=1\n```\n"
    try:
        convert_static(bad_qmd)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "model-*" in str(e)


# ════════════════════════════════════
# convert_fig_cell — Idempotence
# ════════════════════════════════════

FIG_WITH_PLT_SHOW = """@render.plot(alt="Existing")
def fig_test():
    m = model()
    fig, ax = plt.subplots()
    ax.plot([1], [2])
    plt.show()
    return fig
"""


def test_convert_fig_idempotent_plt_show():
    """Should not add duplicate plt.show() when already present."""
    result = convert_fig_cell(FIG_WITH_PLT_SHOW)
    assert result.count("plt.show()") == 1


# ════════════════════════════════════
# detect_model_module — Third pattern
# ════════════════════════════════════

def test_detect_direct_return_module_func():
    """Detect 'return lib.compute(p)' direct call pattern."""
    cells = [{
        "type": "python", "label": "model-reactive",
        "code": "import mylib\nreturn mylib.run(p)",
    }]
    result = detect_model_module(cells)
    assert result == ("mylib", "run")


# ════════════════════════════════════
# write_templates
# ════════════════════════════════════

def test_write_templates_creates_files(tmp_path):
    from shinystatic.core import write_templates

    d = tmp_path / "tpl"
    write_templates(str(d), {"title": "Test", "subtitle": "Subtitle", "author": "Author", "date": "2026"})

    pre = (d / "typst-preamble.typ").read_text()
    cov = (d / "typst-cover.typ").read_text()

    assert "Noto Sans CJK SC" in pre
    assert "first-line-indent" in pre
    assert "Test" in cov
    assert "Subtitle" in cov
    assert "Author" in cov
    assert "pagebreak" in cov


def test_write_templates_default_metadata(tmp_path):
    from shinystatic.core import write_templates

    d = tmp_path / "tpl2"
    write_templates(str(d))

    cov = (d / "typst-cover.typ").read_text()
    assert "Untitled" in cov


# ════════════════════════════════════
# Real file integration tests
# ════════════════════════════════════

def test_static_output_valid_qmd(feasibility_qmd):
    """Generated static .qmd should be a valid Quarto document."""
    result, _ = convert_static(feasibility_qmd)
    # Must start with YAML header
    assert result.startswith("---")
    # Must contain parameters tag
    assert "#| tags: [parameters]" in result
    # Must be renderable (at least syntactically correct)
    _, body = parse_yaml(result)
    cells = parse_cells(body)
    labels = [c["label"] for c in cells if c["type"] == "python" and c["label"]]
    assert "parameters" in labels
    assert "setup-static" in labels
    assert "model-static" in labels


def test_express_output_imports_model(feasibility_qmd):
    """Express output should import model correctly."""
    result = generate_express(feasibility_qmd)
    assert "import model as mlib" in result
    assert "shiny.express" in result


def test_roundtrip_metadata_preserved(feasibility_qmd):
    """Metadata should be preserved after conversion."""
    _, meta = convert_static(feasibility_qmd)
    assert meta["title"] == "Heavy/Medium-Duty Truck Supercharging Station Feasibility Analysis"
    assert "Dongguan" in meta["subtitle"]


# ════════════════════════════════════
# convert_static — Explicit params
# ════════════════════════════════════

def test_convert_static_with_explicit_params(feasibility_qmd):
    """Passing params dict should override DEFAULTS."""
    _, meta = convert_static(feasibility_qmd, {"n_heavy": 99})
    # No error is sufficient


# ════════════════════════════════════
# convert_fig_cell — No function body
# ════════════════════════════════════

def test_convert_fig_no_function():
    """Return empty when no def statement."""
    result = convert_fig_cell("x = 1")
    assert result == ""


# ════════════════════════════════════
# detect_imports — No setup cell
# ════════════════════════════════════

def test_detect_imports_no_setup():
    from shinystatic.core import detect_imports
    cells = [{"type": "python", "label": "text-intro", "code": "x = 1"}]
    result = detect_imports(cells)
    assert result == ""


# ════════════════════════════════════
# generate_setup_cell
# ════════════════════════════════════

def test_generate_setup_cell_with_rcparams():
    from shinystatic.core import generate_setup_cell
    imports = "import numpy as np\nmpl.rcParams['font.sans-serif'] = ['A']"
    result = generate_setup_cell(imports)
    assert "import numpy" in result
    # Already has mpl.rcParams, should not duplicate
    assert result.count("mpl.rcParams") == 1


def test_generate_setup_cell_without_rcparams():
    from shinystatic.core import generate_setup_cell
    result = generate_setup_cell("import numpy as np")
    assert result.count("mpl.rcParams") == 3  # Auto-add three lines


# ════════════════════════════════════
# generate_model_cell
# ════════════════════════════════════

def test_generate_model_cell():
    from shinystatic.core import generate_model_cell
    result = generate_model_cell("mlib", "compute")
    assert "mlib.compute" in result
    assert "_params" in result
    assert "#| label: model-static" in result
