/**
 * Integracion con Obsidian (lee/escribe archivos Markdown en el vault).
 * Obsidian es simplemente una carpeta con archivos .md — no necesita API.
 */

import fs from 'fs';
import path from 'path';

export class ObsidianVault {
    constructor(vaultPath) {
        this.vaultPath = vaultPath;
        this.agendaDir = path.join(vaultPath, 'Agenda');
        this.ensureDirs();
    }

    ensureDirs() {
        if (!fs.existsSync(this.agendaDir)) {
            fs.mkdirSync(this.agendaDir, { recursive: true });
        }
    }

    // ─── AGENDA ────────────────────────────────────────────

    /**
     * Obtiene la ruta del archivo de agenda para una fecha.
     * Formato: Agenda/2026-04-06.md
     */
    getAgendaPath(date) {
        const dateStr = this.formatDate(date);
        return path.join(this.agendaDir, `${dateStr}.md`);
    }

    /**
     * Agrega un compromiso a la agenda de un dia.
     */
    addEvent(date, time, description, category = 'general') {
        const filePath = this.getAgendaPath(date);
        const dateStr = this.formatDate(date);
        const dayName = this.getDayName(date);

        let content = '';
        if (fs.existsSync(filePath)) {
            content = fs.readFileSync(filePath, 'utf-8');
        } else {
            // Crear encabezado del dia
            content = `# Agenda ${dayName} ${dateStr}\n\n`;
        }

        // Agregar el evento
        const tag = `#${category}`;
        const timeStr = time || 'Todo el dia';
        const entry = `- [ ] **${timeStr}** — ${description} ${tag}\n`;

        // Insertar antes del final
        content += entry;

        fs.writeFileSync(filePath, content, 'utf-8');
        return { dateStr, timeStr, description, category };
    }

    /**
     * Lista los compromisos de un dia.
     */
    getEvents(date) {
        const filePath = this.getAgendaPath(date);
        if (!fs.existsSync(filePath)) {
            return [];
        }

        const content = fs.readFileSync(filePath, 'utf-8');
        const lines = content.split('\n');
        const events = [];

        for (const line of lines) {
            const match = line.match(/^- \[( |x)\] \*\*(.+?)\*\* — (.+?)(?:\s+#(\w+))?$/);
            if (match) {
                events.push({
                    done: match[1] === 'x',
                    time: match[2],
                    description: match[3].trim(),
                    category: match[4] || 'general',
                });
            }
        }
        return events;
    }

    /**
     * Lista compromisos de la semana.
     */
    getWeekEvents(fromDate = new Date()) {
        const events = [];
        for (let i = 0; i < 7; i++) {
            const date = new Date(fromDate);
            date.setDate(date.getDate() + i);
            const dayEvents = this.getEvents(date);
            if (dayEvents.length > 0) {
                events.push({
                    date: this.formatDate(date),
                    day: this.getDayName(date),
                    events: dayEvents,
                });
            }
        }
        return events;
    }

    /**
     * Marca un compromiso como completado.
     */
    completeEvent(date, index) {
        const filePath = this.getAgendaPath(date);
        if (!fs.existsSync(filePath)) return false;

        let content = fs.readFileSync(filePath, 'utf-8');
        const lines = content.split('\n');
        let eventCount = 0;

        for (let i = 0; i < lines.length; i++) {
            if (lines[i].match(/^- \[ \]/)) {
                if (eventCount === index) {
                    lines[i] = lines[i].replace('- [ ]', '- [x]');
                    fs.writeFileSync(filePath, lines.join('\n'), 'utf-8');
                    return true;
                }
                eventCount++;
            }
        }
        return false;
    }

    // ─── NOTAS RAPIDAS ─────────────────────────────────────

    /**
     * Crea una nota rapida en el vault.
     */
    addNote(title, content) {
        const notesDir = path.join(this.vaultPath, 'Notas WhatsApp');
        if (!fs.existsSync(notesDir)) {
            fs.mkdirSync(notesDir, { recursive: true });
        }

        const dateStr = this.formatDate(new Date());
        const timeStr = new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
        const safeTitle = title.replace(/[<>:"/\\|?*]/g, '_').substring(0, 50);
        const filePath = path.join(notesDir, `${dateStr} ${safeTitle}.md`);

        const md = `# ${title}\n\n**Fecha**: ${dateStr} ${timeStr}\n**Via**: WhatsApp\n\n---\n\n${content}\n`;
        fs.writeFileSync(filePath, md, 'utf-8');
        return filePath;
    }

    // ─── UTILIDADES ────────────────────────────────────────

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    getDayName(date) {
        const days = ['Domingo', 'Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'];
        return days[date.getDay()];
    }

    /**
     * Parsea una fecha desde texto natural.
     * "hoy", "manana", "lunes", "15/04", "2026-04-15"
     */
    parseDate(text) {
        const lower = text.toLowerCase().trim();
        const now = new Date();

        if (lower === 'hoy') return now;
        if (lower === 'mañana' || lower === 'manana') {
            const d = new Date(now); d.setDate(d.getDate() + 1); return d;
        }
        if (lower === 'pasado mañana' || lower === 'pasado manana') {
            const d = new Date(now); d.setDate(d.getDate() + 2); return d;
        }

        // Dia de la semana
        const days = { 'lunes': 1, 'martes': 2, 'miercoles': 3, 'jueves': 4, 'viernes': 5, 'sabado': 6, 'domingo': 0 };
        if (days[lower] !== undefined) {
            const target = days[lower];
            const current = now.getDay();
            let diff = target - current;
            if (diff <= 0) diff += 7;
            const d = new Date(now); d.setDate(d.getDate() + diff); return d;
        }

        // dd/mm
        const ddmm = lower.match(/^(\d{1,2})\/(\d{1,2})$/);
        if (ddmm) {
            return new Date(now.getFullYear(), parseInt(ddmm[2]) - 1, parseInt(ddmm[1]));
        }

        // ISO
        const iso = Date.parse(lower);
        if (!isNaN(iso)) return new Date(iso);

        return now;
    }
}
