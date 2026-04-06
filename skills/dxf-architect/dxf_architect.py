#!/usr/bin/env python3
"""
DXF Architect Skill - Genera y lee planos arquitectonicos en formato DXF.
Usa ezdxf para crear archivos compatibles con AutoCAD, LibreCAD, BricsCAD.
"""

import ezdxf
from ezdxf import units
from ezdxf.math import Vec2
import os
import json
from typing import Optional


# ─── LECTURA DE DXF ─────────────────────────────────────────────────────────

def read_dxf(filepath: str) -> dict:
    """Lee un archivo DXF y retorna un resumen de su contenido."""
    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()

    summary = {
        "archivo": os.path.basename(filepath),
        "version": doc.dxfversion,
        "capas": [],
        "entidades": {},
        "bloques": [],
        "total_entidades": 0,
    }

    # Capas
    for layer in doc.layers:
        summary["capas"].append({
            "nombre": layer.dxf.name,
            "color": layer.dxf.color,
            "activa": not layer.is_off,
        })

    # Contar entidades por tipo
    for entity in msp:
        etype = entity.dxftype()
        summary["entidades"][etype] = summary["entidades"].get(etype, 0) + 1
        summary["total_entidades"] += 1

    # Bloques
    for block in doc.blocks:
        if not block.name.startswith("*"):
            summary["bloques"].append(block.name)

    return summary


def extract_dimensions(filepath: str) -> list:
    """Extrae todas las cotas de un archivo DXF."""
    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()
    dims = []
    for entity in msp.query("DIMENSION"):
        dims.append({
            "tipo": entity.dxf.dimtype if hasattr(entity.dxf, "dimtype") else "linear",
            "texto": entity.dxf.text if hasattr(entity.dxf, "text") else "",
            "insercion": list(entity.dxf.insert) if hasattr(entity.dxf, "insert") else [],
        })
    return dims


def extract_layers_detail(filepath: str) -> list:
    """Extrae detalle de todas las capas y cuantas entidades tiene cada una."""
    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()

    layer_counts = {}
    for entity in msp:
        layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else "0"
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    result = []
    for layer in doc.layers:
        name = layer.dxf.name
        result.append({
            "nombre": name,
            "color": layer.dxf.color,
            "entidades": layer_counts.get(name, 0),
        })
    return result


# ─── CREACION DE PLANOS ─────────────────────────────────────────────────────

def create_architectural_plan(
    filename: str,
    rooms: list[dict],
    title: str = "PLANO ARQUITECTONICO",
    scale: str = "1:100",
    author: str = "DXF Architect Skill",
    output_dir: str = ".",
) -> str:
    """
    Crea un plano arquitectonico completo en DXF.

    rooms: lista de diccionarios con:
        - nombre: str (ej: "Sala")
        - x: float (posicion X esquina inferior izq)
        - y: float (posicion Y esquina inferior izq)
        - ancho: float (en metros)
        - alto: float (en metros)
        - puertas: list[dict] opcional (pared: "norte"|"sur"|"este"|"oeste", posicion: float 0-1)
        - ventanas: list[dict] opcional (pared: "norte"|"sur"|"este"|"oeste", posicion: float 0-1, ancho: float)
    """
    doc = ezdxf.new("R2010")
    doc.units = units.M
    msp = doc.modelspace()

    # ─── Crear capas ────────────────────────────────────────
    layers = {
        "MUROS": {"color": 7, "lineweight": 50},       # Blanco, grueso
        "COTAS": {"color": 3, "lineweight": 13},       # Verde
        "TEXTOS": {"color": 5, "lineweight": 13},      # Azul
        "PUERTAS": {"color": 1, "lineweight": 25},     # Rojo
        "VENTANAS": {"color": 4, "lineweight": 25},    # Cyan
        "EJES": {"color": 2, "lineweight": 13},        # Amarillo
        "CAJETIN": {"color": 7, "lineweight": 25},     # Blanco
        "MOBILIARIO": {"color": 8, "lineweight": 13},  # Gris
    }

    for name, props in layers.items():
        doc.layers.add(name, color=props["color"], lineweight=props["lineweight"])

    # ─── Dibujar habitaciones ───────────────────────────────
    wall_thickness = 0.15  # 15 cm

    for room in rooms:
        x = room["x"]
        y = room["y"]
        w = room["ancho"]
        h = room["alto"]
        nombre = room.get("nombre", "")

        # Muros exteriores (rectangulo)
        _draw_wall_rect(msp, x, y, w, h, wall_thickness)

        # Nombre de la habitacion
        cx = x + w / 2
        cy = y + h / 2
        msp.add_text(
            nombre,
            dxfattribs={
                "layer": "TEXTOS",
                "height": 0.20,
                "insert": (cx, cy),
                "halign": ezdxf.const.CENTER,
                "valign": ezdxf.const.MIDDLE,
                "align_point": (cx, cy),
            },
        )

        # Area
        area = w * h
        msp.add_text(
            f"{area:.1f} m2",
            dxfattribs={
                "layer": "TEXTOS",
                "height": 0.15,
                "insert": (cx, cy - 0.35),
                "halign": ezdxf.const.CENTER,
                "valign": ezdxf.const.MIDDLE,
                "align_point": (cx, cy - 0.35),
            },
        )

        # Cotas
        _add_dimensions(msp, x, y, w, h)

        # Puertas
        for puerta in room.get("puertas", []):
            _draw_door(msp, x, y, w, h, puerta)

        # Ventanas
        for ventana in room.get("ventanas", []):
            _draw_window(msp, x, y, w, h, ventana)

    # ─── Cajetin (cuadro de datos) ──────────────────────────
    _draw_title_block(msp, title, scale, author, rooms)

    # ─── Guardar ────────────────────────────────────────────
    filepath = os.path.join(output_dir, filename)
    doc.saveas(filepath)
    return os.path.abspath(filepath)


def _draw_wall_rect(msp, x, y, w, h, thickness):
    """Dibuja un rectangulo de muros con grosor."""
    # Muro exterior
    points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    msp.add_lwpolyline(points, dxfattribs={"layer": "MUROS"})

    # Muro interior (offset)
    t = thickness
    inner = [
        (x + t, y + t),
        (x + w - t, y + t),
        (x + w - t, y + h - t),
        (x + t, y + h - t),
        (x + t, y + t),
    ]
    msp.add_lwpolyline(inner, dxfattribs={"layer": "MUROS"})


def _add_dimensions(msp, x, y, w, h):
    """Agrega cotas a una habitacion."""
    offset = 0.5

    # Cota horizontal (abajo)
    msp.add_linear_dim(
        base=(x, y - offset),
        p1=(x, y),
        p2=(x + w, y),
        dimstyle="EZDXF",
        override={"dimtxt": 0.15},
        dxfattribs={"layer": "COTAS"},
    ).render()

    # Cota vertical (izquierda)
    msp.add_linear_dim(
        base=(x - offset, y),
        p1=(x, y),
        p2=(x, y + h),
        angle=90,
        dimstyle="EZDXF",
        override={"dimtxt": 0.15},
        dxfattribs={"layer": "COTAS"},
    ).render()


def _draw_door(msp, x, y, w, h, puerta):
    """Dibuja una puerta con arco de apertura."""
    pared = puerta.get("pared", "sur")
    pos = puerta.get("posicion", 0.5)
    door_width = puerta.get("ancho", 0.90)

    if pared == "sur":
        dx = x + w * pos - door_width / 2
        # Hueco en muro (linea de ruptura)
        msp.add_line((dx, y), (dx + door_width, y), dxfattribs={"layer": "PUERTAS"})
        # Arco de apertura
        msp.add_arc(
            center=(dx, y),
            radius=door_width,
            start_angle=0,
            end_angle=90,
            dxfattribs={"layer": "PUERTAS"},
        )
    elif pared == "norte":
        dx = x + w * pos - door_width / 2
        msp.add_line((dx, y + h), (dx + door_width, y + h), dxfattribs={"layer": "PUERTAS"})
        msp.add_arc(
            center=(dx + door_width, y + h),
            radius=door_width,
            start_angle=90,
            end_angle=180,
            dxfattribs={"layer": "PUERTAS"},
        )
    elif pared == "este":
        dy = y + h * pos - door_width / 2
        msp.add_line((x + w, dy), (x + w, dy + door_width), dxfattribs={"layer": "PUERTAS"})
        msp.add_arc(
            center=(x + w, dy),
            radius=door_width,
            start_angle=90,
            end_angle=180,
            dxfattribs={"layer": "PUERTAS"},
        )
    elif pared == "oeste":
        dy = y + h * pos - door_width / 2
        msp.add_line((x, dy), (x, dy + door_width), dxfattribs={"layer": "PUERTAS"})
        msp.add_arc(
            center=(x, dy + door_width),
            radius=door_width,
            start_angle=270,
            end_angle=360,
            dxfattribs={"layer": "PUERTAS"},
        )


def _draw_window(msp, x, y, w, h, ventana):
    """Dibuja una ventana (doble linea con ruptura)."""
    pared = ventana.get("pared", "sur")
    pos = ventana.get("posicion", 0.5)
    win_width = ventana.get("ancho", 1.20)
    t = 0.08  # grosor simbolo ventana

    if pared == "sur":
        wx = x + w * pos - win_width / 2
        wy = y
        msp.add_line((wx, wy - t), (wx + win_width, wy - t), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx, wy + t), (wx + win_width, wy + t), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx, wy - t), (wx, wy + t), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx + win_width, wy - t), (wx + win_width, wy + t), dxfattribs={"layer": "VENTANAS"})
    elif pared == "norte":
        wx = x + w * pos - win_width / 2
        wy = y + h
        msp.add_line((wx, wy - t), (wx + win_width, wy - t), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx, wy + t), (wx + win_width, wy + t), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx, wy - t), (wx, wy + t), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx + win_width, wy - t), (wx + win_width, wy + t), dxfattribs={"layer": "VENTANAS"})
    elif pared == "este":
        wy = y + h * pos - win_width / 2
        wx = x + w
        msp.add_line((wx - t, wy), (wx - t, wy + win_width), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx + t, wy), (wx + t, wy + win_width), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx - t, wy), (wx + t, wy), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx - t, wy + win_width), (wx + t, wy + win_width), dxfattribs={"layer": "VENTANAS"})
    elif pared == "oeste":
        wy = y + h * pos - win_width / 2
        wx = x
        msp.add_line((wx - t, wy), (wx - t, wy + win_width), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx + t, wy), (wx + t, wy + win_width), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx - t, wy), (wx + t, wy), dxfattribs={"layer": "VENTANAS"})
        msp.add_line((wx - t, wy + win_width), (wx + t, wy + win_width), dxfattribs={"layer": "VENTANAS"})


def _draw_title_block(msp, title, scale, author, rooms):
    """Dibuja un cajetin / cuadro de datos."""
    # Calcular posicion del cajetin (abajo a la derecha)
    max_x = max(r["x"] + r["ancho"] for r in rooms) if rooms else 10
    max_y = min(r["y"] for r in rooms) if rooms else 0

    bx = max_x + 2
    by = max_y - 3
    bw = 8
    bh = 4

    # Marco
    msp.add_lwpolyline(
        [(bx, by), (bx + bw, by), (bx + bw, by + bh), (bx, by + bh), (bx, by)],
        dxfattribs={"layer": "CAJETIN"},
    )

    # Lineas divisoras
    msp.add_line((bx, by + 2.5), (bx + bw, by + 2.5), dxfattribs={"layer": "CAJETIN"})
    msp.add_line((bx, by + 1.5), (bx + bw, by + 1.5), dxfattribs={"layer": "CAJETIN"})
    msp.add_line((bx, by + 0.75), (bx + bw, by + 0.75), dxfattribs={"layer": "CAJETIN"})

    # Textos
    _add_block_text(msp, bx + bw / 2, by + 3.25, title, 0.30)
    _add_block_text(msp, bx + bw / 2, by + 2.0, f"ESCALA: {scale}", 0.18)
    _add_block_text(msp, bx + bw / 2, by + 1.1, f"AUTOR: {author}", 0.15)

    total_area = sum(r["ancho"] * r["alto"] for r in rooms)
    _add_block_text(msp, bx + bw / 2, by + 0.35, f"AREA TOTAL: {total_area:.1f} m2", 0.15)


def _add_block_text(msp, x, y, text, height):
    msp.add_text(
        text,
        dxfattribs={
            "layer": "CAJETIN",
            "height": height,
            "insert": (x, y),
            "halign": ezdxf.const.CENTER,
            "valign": ezdxf.const.MIDDLE,
            "align_point": (x, y),
        },
    )


# ─── EJEMPLO DE USO ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Casa ejemplo: 2 recamaras, sala, cocina, bano
    casa = [
        {
            "nombre": "SALA-COMEDOR",
            "x": 0, "y": 0,
            "ancho": 5.0, "alto": 4.0,
            "puertas": [{"pared": "sur", "posicion": 0.5, "ancho": 1.0}],
            "ventanas": [{"pared": "norte", "posicion": 0.5, "ancho": 1.5}],
        },
        {
            "nombre": "COCINA",
            "x": 5.0, "y": 0,
            "ancho": 3.5, "alto": 4.0,
            "puertas": [{"pared": "oeste", "posicion": 0.5, "ancho": 0.9}],
            "ventanas": [{"pared": "este", "posicion": 0.5, "ancho": 1.2}],
        },
        {
            "nombre": "RECAMARA 1",
            "x": 0, "y": 4.0,
            "ancho": 4.0, "alto": 3.5,
            "puertas": [{"pared": "sur", "posicion": 0.7, "ancho": 0.9}],
            "ventanas": [{"pared": "norte", "posicion": 0.5, "ancho": 1.5}],
        },
        {
            "nombre": "RECAMARA 2",
            "x": 4.0, "y": 4.0,
            "ancho": 4.5, "alto": 3.5,
            "puertas": [{"pared": "sur", "posicion": 0.3, "ancho": 0.9}],
            "ventanas": [{"pared": "norte", "posicion": 0.5, "ancho": 1.5}],
        },
        {
            "nombre": "BANO",
            "x": 0, "y": 7.5,
            "ancho": 2.5, "alto": 2.0,
            "puertas": [{"pared": "sur", "posicion": 0.5, "ancho": 0.7}],
            "ventanas": [{"pared": "norte", "posicion": 0.5, "ancho": 0.6}],
        },
    ]

    filepath = create_architectural_plan(
        filename="casa_ejemplo.dxf",
        rooms=casa,
        title="CASA HABITACION - PLANTA ARQUITECTONICA",
        scale="1:100",
        author="Claude Code / DXF Architect",
        output_dir="/home/user/clowbot/skills/dxf-architect",
    )
    print(f"Plano generado: {filepath}")

    # Leer el plano generado
    info = read_dxf(filepath)
    print(json.dumps(info, indent=2, ensure_ascii=False))
