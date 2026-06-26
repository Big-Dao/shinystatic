"""Comprehensive tests for convert_text_cell — the most complex conversion function."""

from shinystatic.core import convert_text_cell


# ═══════════════════════════
# Basic: simple value access
# ═══════════════════════════

TEXT_SIMPLE = '''@render.ui
def text_intro():
    m = model()
    return ui.markdown(f"""The value of X is {m['x']}.""")'''


def test_simple_key_no_format():
    result = convert_text_cell(TEXT_SIMPLE)
    assert "m['x']" in result
    assert "{python}" in result
    assert "@render" not in result
    assert "ui.markdown" not in result


# ═══════════════════════════
# Format specs (f-string :fmt)
# ═══════════════════════════

TEXT_FORMAT = """@render.ui
def text_fmt():
    m = model()
    return ui.markdown(f\"\"\"Y is {m['y']:.1f}, Z is {m['z']/1000:,.0f}.\"\"\")"""


def test_format_spec_wrapped_in_fstring():
    result = convert_text_cell(TEXT_FORMAT)
    # Expressions with : should be wrapped in f"..."
    assert 'f"{' in result
    assert ':,.0f' in result
    assert ':.1f' in result


def test_format_spec_values_preserved():
    result = convert_text_cell(TEXT_FORMAT)
    assert "m['y']" in result
    assert "m['z']/1000" in result


# ═══════════════════════════
# Multi-line text
# ═══════════════════════════

TEXT_MULTILINE = """@render.ui
def text_multi():
    m = model()
    return ui.markdown(f\"\"\"First line {m['a']}
Second line {m['b']}.\"\"\")"""


def test_multiline_text():
    result = convert_text_cell(TEXT_MULTILINE)
    assert "First line" in result
    assert "Second line" in result


# ═══════════════════════════
# Local variable expansion
# ═══════════════════════════

TEXT_LOCALS = """@render.ui
def text_locals():
    m = model()
    total = m['a'] + m['b']
    rate = m['c'] * 100
    return ui.markdown(f\"\"\"Total {total:.0f}, rate {rate:.1f}%.\"\"\")"""


def test_locals_expanded():
    result = convert_text_cell(TEXT_LOCALS)
    # Local variable references should be expanded to expressions
    assert "total" not in result.split("{python}")[-1].split("`")[0]  # Should not retain total
    assert "m['a'] + m['b']" in result  # Appears after expansion
    assert "m['c'] * 100" in result


def test_locals_not_confused_with_m():
    """m assignment should not be expanded as a local variable."""
    result = convert_text_cell(TEXT_LOCALS)
    # m itself is reserved
    assert "m['a']" in result


# ═══════════════════════════
# No f-string → return empty
# ═══════════════════════════

TEXT_NO_FSTRING = """@render.ui
def text_empty():
    return None"""


def test_no_fstring_returns_empty():
    result = convert_text_cell(TEXT_NO_FSTRING)
    assert result == ""


# ═══════════════════════════
# Single-quote f-string (f'''...''')
# ═══════════════════════════

TEXT_SINGLE_QUOTE = """@render.ui
def text_sq():
    m = model()
    return ui.markdown(f'''X = {m['x']}.''')"""


def test_single_quote_fstring():
    result = convert_text_cell(TEXT_SINGLE_QUOTE)
    assert "m['x']" in result
    assert "{python}" in result


# ═══════════════════════════
# Mixed: local variables + direct references + format specs
# ═══════════════════════════

TEXT_MIXED = """@render.ui
def text_mixed():
    m = model()
    unit = m['fee'] + m['sell'] - m['buy']
    return ui.markdown(f\"\"\"Unit price {unit:.2f} CNY/kWh.
Service fee {m['fee']:.2f} CNY, selling price {m['sell']} CNY,
purchase price {m['buy']} CNY, total user payment {m['fee'] + m['sell']:.2f} CNY.\"\"\")"""


def test_mixed_all_patterns():
    result = convert_text_cell(TEXT_MIXED)
    # Local variable expansion
    assert "m['fee'] + m['sell'] - m['buy']" in result
    # Format spec wrapping
    assert 'f"{"' in result or 'f\"' in result
    # Simple references preserved
    assert "m['sell']" in result


# ═══════════════════════════
# Newline escaping
# ═══════════════════════════

TEXT_NEWLINE = (
    "@render.ui\n"
    "def text_nl():\n"
    "    m = model()\n"
    "    return ui.markdown(f\"\"\"CAPEX {m['capex']/1e4:,.0f} 10k CNY\\nNPV {m['npv']/1e4:,.0f} 10k CNY\"\"\")\n"
)


def test_newline_unescaped():
    result = convert_text_cell(TEXT_NEWLINE)
    assert "\\n" not in result


# ═══════════════════════════
# Markdown format preserved
# ═══════════════════════════

TEXT_MARKDOWN = """@render.ui
def text_md():
    m = model()
    return ui.markdown(f\"\"\"- **Important**: {m['x']}
> Quote: {m['y']:.0f}.\"\"\")"""


def test_markdown_preserved():
    result = convert_text_cell(TEXT_MARKDOWN)
    assert "**Important**" in result
    assert "> Quote" in result


# ═══════════════════════════
# No return statement → no local variable extraction → normal output
# ═══════════════════════════

TEXT_NO_RETURN = """@render.ui
def text_nr():
    return ui.markdown(f\"\"\"X = {m['x']}\"\"\")"""


def test_no_locals_still_converts():
    """Text should still convert normally even without local variable definitions."""
    result = convert_text_cell(TEXT_NO_RETURN)
    assert "{python}" in result
    assert "m['x']" in result
