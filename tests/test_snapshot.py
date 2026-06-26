"""Snapshot tests — guard against accidental output regression.

Each run compares output byte-for-byte against snapshots/.
First run or after output changes: pytest --snapshot-update
"""

import pytest
from shinystatic.core import convert_static, generate_express, generate_parameters_cell


# ═══════════════════════════════════════════
# Static conversion snapshots
# ═══════════════════════════════════════════

def test_feasibility_static_snapshot(snapshot, feasibility_qmd):
    """feasibility.qmd static conversion output must be stable."""
    result, _ = convert_static(feasibility_qmd)
    snapshot.assert_match(result, "feasibility-static.qmd")


def test_feasibility_express_snapshot(snapshot, feasibility_qmd):
    """feasibility.qmd Express output must be stable."""
    result = generate_express(feasibility_qmd)
    snapshot.assert_match(result, "feasibility_express.py")


# ═══════════════════════════════════════════
# Parameters cell snapshots
# ═══════════════════════════════════════════

def test_parameters_cell_snapshot(snapshot):
    """Parameters cell generation format must be stable."""
    defaults = {
        "x": 10, "y": 3.14, "label": "Test",
        "items": [1, 2, 3], "flag": True,
    }
    result = generate_parameters_cell(defaults)
    snapshot.assert_match(result, "parameters-cell.qmd")


# ═══════════════════════════════════════════
# Minimal document snapshots
# ═══════════════════════════════════════════

def test_minimal_static_snapshot(snapshot, minimal_qmd):
    """Minimal .qmd static conversion output must be stable."""
    result, _ = convert_static(minimal_qmd)
    snapshot.assert_match(result, "minimal-static.qmd")
