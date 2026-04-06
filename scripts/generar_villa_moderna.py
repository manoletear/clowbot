#!/usr/bin/env python3
"""
Genera planos DXF de villa moderna de 2 pisos basada en analisis de imagen.
Estilo contemporaneo, volumetria cubica escalonada, piscina frontal.
Dimensiones estimadas: 14m x 11m aprox.
"""

import sys
sys.path.insert(0, "/home/user/clowbot")

import ezdxf
from ezdxf import units

OUTPUT_DIR = "/home/user/clowbot/skills/dxf-architect"


def setup_doc():
    doc = ezdxf.new("R2010")
    doc.units = units.M

    layers = {
        "MUROS": {"color": 7, "lineweight": 50},
        "MUROS_INT": {"color": 9, "lineweight": 30},
        "COTAS": {"color": 3, "lineweight": 13},
        "TEXTOS": {"color": 5, "lineweight": 13},
        "PUERTAS": {"color": 1, "lineweight": 25},
        "VENTANAS": {"color": 4, "lineweight": 25},
        "EJES": {"color": 2, "lineweight": 13},
        "CAJETIN": {"color": 7, "lineweight": 25},
        "PISCINA": {"color": 150, "lineweight": 30},
        "TERRAZA": {"color": 8, "lineweight": 13},
        "MOBILIARIO": {"color": 8, "lineweight": 13},
        "ESCALERA": {"color": 6, "lineweight": 25},
    }
    for name, props in layers.items():
        doc.layers.add(name, color=props["color"], lineweight=props["lineweight"])

    return doc


def add_text(msp, x, y, text, height=0.20, layer="TEXTOS"):
    msp.add_text(
        text,
        dxfattribs={
            "layer": layer,
            "height": height,
            "insert": (x, y),
            "halign": ezdxf.const.CENTER,
            "valign": ezdxf.const.MIDDLE,
            "align_point": (x, y),
        },
    )


def draw_room(msp, x, y, w, h, name, area=None, layer="MUROS"):
    """Dibuja una habitacion con muros."""
    points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    msp.add_lwpolyline(points, dxfattribs={"layer": layer})
    add_text(msp, x + w / 2, y + h / 2, name)
    if area is None:
        area = w * h
    add_text(msp, x + w / 2, y + h / 2 - 0.35, f"{area:.1f} m2", 0.15)


def draw_door(msp, x, y, angle_start, angle_end, radius=0.9):
    """Puerta con arco de apertura."""
    msp.add_arc(
        center=(x, y), radius=radius,
        start_angle=angle_start, end_angle=angle_end,
        dxfattribs={"layer": "PUERTAS"},
    )


def draw_window(msp, x1, y1, x2, y2):
    """Ventana como doble linea."""
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "VENTANAS"})
    # Lineas paralelas para simbolo de ventana
    dx = (y2 - y1) * 0.06
    dy = (x2 - x1) * 0.06
    msp.add_line((x1 + dx, y1 - dy), (x2 + dx, y2 - dy), dxfattribs={"layer": "VENTANAS"})
    msp.add_line((x1 - dx, y1 + dy), (x2 - dx, y2 + dy), dxfattribs={"layer": "VENTANAS"})


def draw_sliding_door(msp, x1, y1, x2, y2):
    """Puerta corrediza (linea con flechas)."""
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "VENTANAS"})
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "PUERTAS"})
    # Doble linea simbolo corrediza
    dx = (y2 - y1) * 0.04
    dy = (x2 - x1) * 0.04
    msp.add_line((x1 + dx, y1 - dy), (x2 + dx, y2 - dy), dxfattribs={"layer": "PUERTAS"})
    msp.add_line((x1 - dx, y1 + dy), (x2 - dx, y2 + dy), dxfattribs={"layer": "PUERTAS"})


def add_dim_h(msp, x1, x2, y, offset=-0.6):
    """Cota horizontal."""
    msp.add_linear_dim(
        base=(x1, y + offset), p1=(x1, y), p2=(x2, y),
        dimstyle="EZDXF", override={"dimtxt": 0.15},
        dxfattribs={"layer": "COTAS"},
    ).render()


def add_dim_v(msp, y1, y2, x, offset=-0.6):
    """Cota vertical."""
    msp.add_linear_dim(
        base=(x + offset, y1), p1=(x, y1), p2=(x, y2),
        angle=90, dimstyle="EZDXF", override={"dimtxt": 0.15},
        dxfattribs={"layer": "COTAS"},
    ).render()


def draw_stairs(msp, x, y, w, h, direction="up"):
    """Escalera con lineas de huella."""
    msp.add_lwpolyline(
        [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)],
        dxfattribs={"layer": "ESCALERA"},
    )
    num_steps = 14
    step_h = h / num_steps
    for i in range(num_steps):
        sy = y + i * step_h
        msp.add_line((x, sy), (x + w, sy), dxfattribs={"layer": "ESCALERA"})
    # Flecha de subida
    add_text(msp, x + w / 2, y + h / 2, "SUBE" if direction == "up" else "BAJA", 0.15, "ESCALERA")


def draw_title_block(msp, bx, by, title, level, scale="1:100"):
    """Cajetin."""
    bw, bh = 8, 4.5
    msp.add_lwpolyline(
        [(bx, by), (bx + bw, by), (bx + bw, by + bh), (bx, by + bh), (bx, by)],
        dxfattribs={"layer": "CAJETIN"},
    )
    msp.add_line((bx, by + 3.0), (bx + bw, by + 3.0), dxfattribs={"layer": "CAJETIN"})
    msp.add_line((bx, by + 2.0), (bx + bw, by + 2.0), dxfattribs={"layer": "CAJETIN"})
    msp.add_line((bx, by + 1.0), (bx + bw, by + 1.0), dxfattribs={"layer": "CAJETIN"})

    add_text(msp, bx + bw / 2, by + 3.75, title, 0.28, "CAJETIN")
    add_text(msp, bx + bw / 2, by + 2.5, level, 0.22, "CAJETIN")
    add_text(msp, bx + bw / 2, by + 1.5, f"ESCALA: {scale}", 0.16, "CAJETIN")
    add_text(msp, bx + bw / 2, by + 0.5, "Claude Code / DXF Architect", 0.14, "CAJETIN")


# ═══════════════════════════════════════════════════════════════════════════
# PLANTA BAJA (1er Piso)
# ═══════════════════════════════════════════════════════════════════════════

def generate_ground_floor():
    doc = setup_doc()
    msp = doc.modelspace()

    # ─── Perimetro exterior 14 x 11 ─────────────────────────
    msp.add_lwpolyline(
        [(0, 0), (14, 0), (14, 11), (0, 11), (0, 0)],
        dxfattribs={"layer": "MUROS"},
    )

    # ─── VESTIBULO / HALL DE ENTRADA ────────────────────────
    # Muro interior separador
    msp.add_line((3.5, 0), (3.5, 3.0), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((3.5, 3.0), (0, 3.0), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 1.75, 1.5, "VESTIBULO")
    add_text(msp, 1.75, 1.15, "6.3 m2", 0.15)
    # Puerta principal (sur)
    draw_door(msp, 1.5, 0, 0, 90, 1.0)

    # ─── SALA - COMEDOR (gran espacio abierto) ──────────────
    # Desde x=3.5 hasta x=14, y=0 hasta y=6
    msp.add_line((3.5, 6.0), (14, 6.0), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((3.5, 3.0), (3.5, 6.0), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 8.75, 3.8, "SALA - COMEDOR")
    add_text(msp, 8.75, 3.4, "63.0 m2", 0.15)

    # Ventanales corredizos al sur (hacia piscina) - 4m
    draw_sliding_door(msp, 5.0, 0, 9.0, 0)
    # Ventanal lateral este
    draw_sliding_door(msp, 14, 1.0, 14, 4.5)

    # ─── COCINA ─────────────────────────────────────────────
    msp.add_line((0, 3.0), (0, 6.0), dxfattribs={"layer": "MUROS"})  # ya es perimetro
    msp.add_line((3.5, 6.0), (0, 6.0), dxfattribs={"layer": "MUROS_INT"})
    # Muro cocina interior ya esta con vestibulo
    add_text(msp, 1.75, 4.5, "COCINA")
    add_text(msp, 1.75, 4.15, "10.5 m2", 0.15)
    # Puerta cocina-vestibulo
    draw_door(msp, 3.5, 3.5, 90, 180, 0.9)
    # Ventana cocina oeste
    draw_window(msp, 0, 3.8, 0, 5.2)

    # Barra/isla de cocina (mobiliario)
    msp.add_lwpolyline(
        [(0.3, 3.2), (3.2, 3.2), (3.2, 3.6), (0.3, 3.6), (0.3, 3.2)],
        dxfattribs={"layer": "MOBILIARIO"},
    )
    add_text(msp, 1.75, 3.4, "mesada", 0.10, "MOBILIARIO")

    # ─── ESTUDIO / OFICINA ──────────────────────────────────
    msp.add_line((10, 6.0), (10, 8.5), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((10, 8.5), (14, 8.5), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 12.0, 7.25, "ESTUDIO")
    add_text(msp, 12.0, 6.9, "10.0 m2", 0.15)
    draw_door(msp, 10, 7.0, 0, 90, 0.9)
    # Ventana este
    draw_window(msp, 14, 6.5, 14, 8.0)

    # ─── BAÑO SOCIAL ────────────────────────────────────────
    msp.add_line((10, 8.5), (10, 11), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((10, 8.5), (12.5, 8.5), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((12.5, 8.5), (12.5, 11), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 11.25, 9.75, "BAÑO")
    add_text(msp, 11.25, 9.4, "6.3 m2", 0.15)
    draw_door(msp, 10.5, 8.5, 270, 360, 0.7)
    # Ventana norte
    draw_window(msp, 10.5, 11, 12.0, 11)

    # ─── LAVANDERIA ─────────────────────────────────────────
    add_text(msp, 13.25, 9.75, "LAVANDERIA")
    add_text(msp, 13.25, 9.4, "3.8 m2", 0.15)
    draw_door(msp, 12.5, 9.0, 0, 90, 0.7)

    # ─── ESCALERA ───────────────────────────────────────────
    draw_stairs(msp, 0, 6.0, 1.5, 3.5, "up")

    # ─── PASILLO / DISTRIBUIDOR ─────────────────────────────
    msp.add_line((1.5, 6.0), (1.5, 11), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 0.75, 10.0, "ESC.", 0.15)

    # ─── TERRAZA POSTERIOR ──────────────────────────────────
    msp.add_line((1.5, 9.5), (10, 9.5), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 5.75, 10.25, "TERRAZA POSTERIOR")
    add_text(msp, 5.75, 9.9, "12.8 m2", 0.15)
    # Puertas corredizas a terraza
    draw_sliding_door(msp, 3.0, 9.5, 6.5, 9.5)

    # ─── CUARTO DE SERVICIO ─────────────────────────────────
    msp.add_line((1.5, 6.0), (5, 6.0), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((5, 6.0), (5, 9.5), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 3.25, 7.75, "CUARTO")
    add_text(msp, 3.25, 7.4, "DE SERVICIO", 0.15)
    add_text(msp, 3.25, 7.05, "12.3 m2", 0.15)
    draw_door(msp, 5, 7.0, 0, 90, 0.9)

    # ─── DISTRIBUIDOR PLANTA BAJA ───────────────────────────
    add_text(msp, 7.5, 7.25, "DISTRIBUIDOR")
    add_text(msp, 7.5, 6.9, "17.5 m2", 0.15)

    # ═══ EXTERIOR: PISCINA ══════════════════════════════════
    # Piscina al sur
    pool_points = [
        (3.0, -1.5), (12.0, -1.5), (12.0, -5.5),
        (3.0, -5.5), (3.0, -1.5),
    ]
    msp.add_lwpolyline(pool_points, dxfattribs={"layer": "PISCINA"})
    add_text(msp, 7.5, -3.5, "PISCINA", 0.25, "PISCINA")
    add_text(msp, 7.5, -3.9, "9.0 x 4.0 m", 0.15, "PISCINA")

    # Jacuzzi circular
    msp.add_circle(center=(2.0, -3.5), radius=1.2, dxfattribs={"layer": "PISCINA"})
    add_text(msp, 2.0, -3.5, "JACUZZI", 0.15, "PISCINA")

    # Terraza de piscina
    terrace = [
        (0, -0.5), (14, -0.5), (14, -6.5), (0, -6.5), (0, -0.5),
    ]
    msp.add_lwpolyline(terrace, dxfattribs={"layer": "TERRAZA"})
    add_text(msp, 13.0, -4.0, "DECK", 0.18, "TERRAZA")

    # Cascada (simbolo)
    msp.add_line((7.0, -1.5), (7.0, -0.5), dxfattribs={"layer": "PISCINA"})
    msp.add_line((8.0, -1.5), (8.0, -0.5), dxfattribs={"layer": "PISCINA"})
    add_text(msp, 7.5, -1.0, "cascada", 0.12, "PISCINA")

    # ─── COTAS GENERALES ────────────────────────────────────
    add_dim_h(msp, 0, 14, 0, -7.5)
    add_dim_v(msp, 0, 11, 0, -1.5)
    add_dim_h(msp, 0, 3.5, 11, 0.6)
    add_dim_h(msp, 3.5, 10, 11, 0.6)
    add_dim_h(msp, 10, 14, 11, 0.6)
    add_dim_v(msp, 0, 6, 14, 0.6)
    add_dim_v(msp, 6, 11, 14, 0.6)

    # ─── CAJETIN ────────────────────────────────────────────
    draw_title_block(msp, 16, -2, "VILLA MODERNA CONTEMPORANEA", "PLANTA BAJA - 1er PISO")

    # ─── EJES ───────────────────────────────────────────────
    for i, label in enumerate(["A", "B", "C", "D"]):
        x = [0, 3.5, 10, 14][i]
        msp.add_line((x, -7), (x, 12), dxfattribs={"layer": "EJES"})
        msp.add_circle(center=(x, 12.5), radius=0.4, dxfattribs={"layer": "EJES"})
        add_text(msp, x, 12.5, label, 0.25, "EJES")

    for i, label in enumerate(["1", "2", "3", "4"]):
        y = [0, 3.0, 6.0, 11.0][i]
        msp.add_line((-2, y), (15, y), dxfattribs={"layer": "EJES"})
        msp.add_circle(center=(-2.5, y), radius=0.4, dxfattribs={"layer": "EJES"})
        add_text(msp, -2.5, y, label, 0.25, "EJES")

    filepath = f"{OUTPUT_DIR}/villa_moderna_planta_baja.dxf"
    doc.saveas(filepath)
    print(f"Planta Baja generada: {filepath}")
    return filepath


# ═══════════════════════════════════════════════════════════════════════════
# PLANTA ALTA (2do Piso)
# ═══════════════════════════════════════════════════════════════════════════

def generate_upper_floor():
    doc = setup_doc()
    msp = doc.modelspace()

    # ─── Perimetro (retranqueado parcialmente) ──────────────
    # Volumen principal: 14 x 11 pero con retranqueo en fachada sur
    # Planta alta retranqueada 2m al sur = terraza balcon
    msp.add_lwpolyline(
        [(0, 2), (14, 2), (14, 11), (0, 11), (0, 2)],
        dxfattribs={"layer": "MUROS"},
    )

    # Balcon/terraza frontal (sobre sala planta baja)
    msp.add_lwpolyline(
        [(0, 0), (14, 0), (14, 2), (0, 2), (0, 0)],
        dxfattribs={"layer": "TERRAZA"},
    )
    add_text(msp, 7, 1.0, "BALCON FRONTAL")
    add_text(msp, 7, 0.65, "28.0 m2", 0.15)
    # Barandal de vidrio (linea punteada conceptual)
    msp.add_line((0, 0), (14, 0), dxfattribs={"layer": "TERRAZA"})

    # ─── RECAMARA PRINCIPAL (MASTER) ────────────────────────
    msp.add_line((0, 2), (0, 7), dxfattribs={"layer": "MUROS"})
    msp.add_line((6.5, 2), (6.5, 7), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((0, 7), (6.5, 7), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 3.25, 4.5, "RECAMARA PRINCIPAL")
    add_text(msp, 3.25, 4.1, "32.5 m2", 0.15)

    # Ventanal master al sur
    draw_sliding_door(msp, 1.0, 2, 5.5, 2)
    # Ventana oeste
    draw_window(msp, 0, 3.0, 0, 5.5)
    # Puerta master
    draw_door(msp, 6.5, 5.5, 90, 180, 0.9)

    # ─── BAÑO MASTER (EN-SUITE) ─────────────────────────────
    msp.add_line((0, 7), (4.5, 7), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((4.5, 7), (4.5, 9.5), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((0, 9.5), (4.5, 9.5), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 2.25, 8.25, "BAÑO MASTER")
    add_text(msp, 2.25, 7.9, "11.3 m2", 0.15)
    draw_door(msp, 4.0, 7.0, 270, 360, 0.8)
    draw_window(msp, 0, 7.5, 0, 9.0)

    # ─── VESTIDOR (WALK-IN CLOSET) ──────────────────────────
    msp.add_line((4.5, 7), (6.5, 7), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((6.5, 7), (6.5, 9.5), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((4.5, 9.5), (6.5, 9.5), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 5.5, 8.25, "VESTIDOR")
    add_text(msp, 5.5, 7.9, "5.0 m2", 0.15)
    draw_door(msp, 5.0, 7.0, 270, 360, 0.7)

    # ─── RECAMARA 2 ─────────────────────────────────────────
    msp.add_line((6.5, 2), (6.5, 5.5), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((6.5, 5.5), (10.5, 5.5), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((10.5, 2), (10.5, 5.5), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 8.5, 3.75, "RECAMARA 2")
    add_text(msp, 8.5, 3.4, "14.0 m2", 0.15)
    draw_door(msp, 10.0, 5.5, 270, 360, 0.9)
    # Ventanal sur
    draw_sliding_door(msp, 7.5, 2, 9.5, 2)

    # ─── RECAMARA 3 ─────────────────────────────────────────
    msp.add_line((10.5, 2), (10.5, 5.5), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((10.5, 5.5), (14, 5.5), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 12.25, 3.75, "RECAMARA 3")
    add_text(msp, 12.25, 3.4, "12.3 m2", 0.15)
    draw_door(msp, 10.5, 4.5, 0, 90, 0.9)
    # Ventana este
    draw_window(msp, 14, 3.0, 14, 5.0)
    # Ventanal sur
    draw_window(msp, 11.0, 2, 13.0, 2)

    # ─── BAÑO COMPARTIDO (Rec 2 y 3) ───────────────────────
    msp.add_line((10.5, 5.5), (10.5, 8), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((10.5, 8), (14, 8), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((6.5, 5.5), (6.5, 8), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((6.5, 8), (10.5, 8), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 8.5, 6.75, "BAÑO 2")
    add_text(msp, 8.5, 6.4, "10.0 m2", 0.15)
    draw_door(msp, 7.0, 8.0, 180, 270, 0.8)
    draw_window(msp, 7.5, 8, 9.5, 8)

    # ─── SALA DE TV / FAMILY ROOM ───────────────────────────
    msp.add_line((10.5, 8), (14, 8), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 12.25, 9.5, "SALA TV")
    add_text(msp, 12.25, 9.15, "10.5 m2", 0.15)
    draw_door(msp, 10.5, 9.0, 0, 90, 0.9)
    draw_window(msp, 14, 8.5, 14, 10.5)

    # ─── ESCALERA ───────────────────────────────────────────
    draw_stairs(msp, 0, 9.5, 1.5, 1.5, "down")

    # ─── PASILLO ────────────────────────────────────────────
    msp.add_line((0, 9.5), (6.5, 9.5), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((6.5, 8), (6.5, 11), dxfattribs={"layer": "MUROS_INT"})
    msp.add_line((10.5, 8), (10.5, 11), dxfattribs={"layer": "MUROS_INT"})
    add_text(msp, 3.5, 10.25, "PASILLO", 0.15)

    # ─── TERRAZA AZOTEA (acceso) ────────────────────────────
    add_text(msp, 8.5, 10.0, "ACC. AZOTEA", 0.15, "TERRAZA")

    # ─── COTAS GENERALES ────────────────────────────────────
    add_dim_h(msp, 0, 14, 2, -1.5)
    add_dim_v(msp, 2, 11, 0, -1.5)
    add_dim_h(msp, 0, 6.5, 11, 0.6)
    add_dim_h(msp, 6.5, 10.5, 11, 0.6)
    add_dim_h(msp, 10.5, 14, 11, 0.6)
    add_dim_v(msp, 2, 5.5, 14, 0.6)
    add_dim_v(msp, 5.5, 8, 14, 0.6)
    add_dim_v(msp, 8, 11, 14, 0.6)

    # ─── EJES ───────────────────────────────────────────────
    for i, label in enumerate(["A", "B", "C", "D"]):
        x = [0, 6.5, 10.5, 14][i]
        msp.add_line((x, -1), (x, 12), dxfattribs={"layer": "EJES"})
        msp.add_circle(center=(x, 12.5), radius=0.4, dxfattribs={"layer": "EJES"})
        add_text(msp, x, 12.5, label, 0.25, "EJES")

    for i, label in enumerate(["1", "2", "3", "4", "5"]):
        y = [0, 2, 5.5, 8, 11][i]
        msp.add_line((-2, y), (15, y), dxfattribs={"layer": "EJES"})
        msp.add_circle(center=(-2.5, y), radius=0.4, dxfattribs={"layer": "EJES"})
        add_text(msp, -2.5, y, label, 0.25, "EJES")

    # ─── CAJETIN ────────────────────────────────────────────
    draw_title_block(msp, 16, 0, "VILLA MODERNA CONTEMPORANEA", "PLANTA ALTA - 2do PISO")

    filepath = f"{OUTPUT_DIR}/villa_moderna_planta_alta.dxf"
    doc.saveas(filepath)
    print(f"Planta Alta generada: {filepath}")
    return filepath


# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    f1 = generate_ground_floor()
    f2 = generate_upper_floor()
    print(f"\nPlanos generados exitosamente:")
    print(f"  1er Piso: {f1}")
    print(f"  2do Piso: {f2}")
