# Clowbot - Herramientas de Arquitectura y Construccion

## Estructura del Proyecto

```
clowbot/
├── mcp-servers/
│   ├── autocad-mcp/          # MCP server para DXF/AutoCAD (Prumputira/autocad-mcp)
│   └── ifc-bonsai-mcp/       # MCP server para BIM/IFC (Show2Instruct/ifc-bonsai-mcp)
├── skills/
│   ├── dxf-architect/         # Skill propia para generar planos DXF
│   │   ├── dxf_architect.py   # Modulo principal
│   │   ├── skill.json         # Metadata de la skill
│   │   └── casa_ejemplo.dxf   # Plano de ejemplo generado
│   └── nano-banana-prompts/   # Skill de Nano Banana Pro (YouMind-OpenLab)
│       ├── references/        # 10,000+ prompts organizados por categoria
│       └── SKILL.md           # Documentacion de uso
├── mcp-config.json            # Configuracion de MCP servers
└── CLAUDE.md                  # Este archivo
```

## MCP Servers Instalados

### 1. autocad-mcp (DXF)
- **Repo**: github.com/Prumputira/autocad-mcp
- **Backend**: ezdxf (headless, no requiere AutoCAD)
- **Capacidades**: 22 tools, ~130 operaciones (dibujo, capas, bloques, cotas, entidades)
- **Uso**: Crear, abrir, editar archivos DXF completos

### 2. ifc-bonsai-mcp (BIM/IFC)
- **Repo**: github.com/Show2Instruct/ifc-bonsai-mcp
- **Capacidades**: 50+ tools para modelos IFC (muros, puertas, techos, analisis)
- **Requiere**: Blender 4.4+ con addon Bonsai 0.8.2+
- **Uso**: Crear y analizar modelos BIM en formato IFC

## Skill DXF Architect

Skill propia para generar planos arquitectonicos DXF con:
- Muros con grosor (15cm)
- Puertas con arco de apertura
- Ventanas (simbolo doble linea)
- Cotas automaticas (horizontal y vertical)
- Textos con nombre de habitacion y area
- Cajetin con titulo, escala, autor y area total
- Capas organizadas (MUROS, COTAS, TEXTOS, PUERTAS, VENTANAS, EJES, CAJETIN, MOBILIARIO)

## Skill Nano Banana Pro Prompts (YouMind-OpenLab)

Biblioteca de 10,000+ prompts curados para generacion de imagenes con Nano Banana Pro (Gemini).

- **Categorias**: social media, e-commerce, YouTube thumbnails, avatares, comics, posters, game assets, infografias, web design
- **Modos**: Busqueda directa por descripcion / Content Remix (pegar articulo y generar prompts)
- **Sincronizacion**: Auto-update via GitHub Actions (2x al dia)
- **Repo**: github.com/YouMind-OpenLab/nano-banana-pro-prompts-recommend-skill

### Uso rapido

```python
from skills.dxf_architect import dxf_architect

rooms = [
    {"nombre": "SALA", "x": 0, "y": 0, "ancho": 5.0, "alto": 4.0,
     "puertas": [{"pared": "sur", "posicion": 0.5}],
     "ventanas": [{"pared": "norte", "posicion": 0.5, "ancho": 1.5}]},
]

dxf_architect.create_architectural_plan("mi_plano.dxf", rooms)
```
