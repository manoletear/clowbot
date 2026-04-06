#!/usr/bin/env python3
"""Exporta los planos DXF de la villa moderna a PDF."""

import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt

DXF_DIR = "/home/user/clowbot/skills/dxf-architect"

files = [
    ("villa_moderna_planta_baja.dxf", "villa_moderna_planta_baja.pdf"),
    ("villa_moderna_planta_alta.dxf", "villa_moderna_planta_alta.pdf"),
]

for dxf_name, pdf_name in files:
    doc = ezdxf.readfile(f"{DXF_DIR}/{dxf_name}")
    msp = doc.modelspace()

    fig = plt.figure(figsize=(24, 18))
    ax = fig.add_axes([0.05, 0.05, 0.9, 0.9])

    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp)

    ax.set_aspect("equal")
    ax.set_facecolor("#ffffff")
    fig.patch.set_facecolor("#ffffff")

    pdf_path = f"{DXF_DIR}/{pdf_name}"
    fig.savefig(pdf_path, dpi=150, bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    print(f"PDF generado: {pdf_path}")
