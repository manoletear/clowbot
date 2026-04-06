# ClowBot — Bot WhatsApp + Obsidian

Bot de WhatsApp que organiza tu agenda escolar y guarda todo en tu vault de Obsidian.

## Instalacion

```bash
cd bot-whatsapp
npm install
```

## Configuracion

Edita `config.js` y cambia la ruta de tu vault de Obsidian:

```js
obsidianVaultPath: 'C:\\Users\\TuNombre\\Documents\\Obsidian\\MiVault'
```

## Ejecutar

```bash
npm start
```

Escanea el QR con tu telefono (WhatsApp > Dispositivos vinculados).

## Comandos

| Comando | Que hace | Ejemplo |
|---------|----------|---------|
| `!agenda [fecha]` | Ver compromisos del dia | `!agenda manana` |
| `!semana` | Ver proximos 7 dias | `!semana` |
| `!agregar <fecha> <hora> <desc>` | Nuevo compromiso | `!agregar lunes 09:00 Examen mate #examen` |
| `!listo <num>` | Marcar como completado | `!listo 1` |
| `!nota <titulo> \| <texto>` | Guardar nota en Obsidian | `!nota Ideas \| Usar React` |
| `!ayuda` | Lista de comandos | `!ayuda` |

## Categorias con hashtags

Agrega `#hashtag` al final del compromiso para categorizarlo:

- `#tarea` — Tareas y deberes
- `#examen` — Examenes y evaluaciones
- `#reunion` — Reuniones
- `#proyecto` — Proyectos

## Estructura en Obsidian

```
MiVault/
├── Agenda/
│   ├── 2026-04-06.md
│   ├── 2026-04-07.md
│   └── ...
└── Notas WhatsApp/
    └── 2026-04-06 Ideas proyecto.md
```

## Fechas validas

- `hoy`, `manana`, `pasado manana`
- Dias: `lunes`, `martes`, `miercoles`, etc.
- Formato: `15/04` o `2026-04-15`
