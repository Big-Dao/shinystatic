"""shinystatic — Convert Shiny Express .qmd to static .qmd (Typst/PDF) or standalone Express apps.

Usage:
    shinystatic doc.qmd --mode express       # Generate standalone Express app
    shinystatic doc.qmd --mode static        # Generate static .qmd
    shinystatic doc.qmd --mode static --render   # Generate + quarto render

Source conventions — cell label prefixes:
    setup       — imports & matplotlib config
    params-*    — DEFAULTS dict (parameter definitions)
    model-*     — @reactive.calc reactive model
    ui-*        — Shiny sidebar / UI widgets (removed in PDF)
    text-*      — @render.ui body text → {python} inline
    fig-*       — @render.plot figures → plt.show()
    tbl-*       — @render.data_frame tables → DataFrame display
    export-*    — export/download buttons (removed in PDF)
"""

from shinystatic.core import convert_static, generate_express
from shinystatic._version import __version__

__all__ = ["convert_static", "generate_express", "main", "__version__"]


def main() -> None:
    from shinystatic.__main__ import main as _main
    _main()
