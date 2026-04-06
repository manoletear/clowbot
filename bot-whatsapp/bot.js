/**
 * ClowBot — Bot de WhatsApp para agenda escolar + Obsidian
 *
 * Comandos:
 *   !agenda [fecha]           — Ver compromisos del dia
 *   !semana                   — Ver compromisos de la semana
 *   !agregar <fecha> <hora> <desc> — Agregar compromiso
 *   !listo <numero>           — Marcar compromiso como hecho
 *   !nota <titulo> | <texto>  — Guardar nota en Obsidian
 *   !ayuda                    — Lista de comandos
 *
 * Configuracion:
 *   Edita config.js para definir la ruta de tu vault de Obsidian
 *   y los grupos donde el bot responde.
 */

import makeWASocket, { useMultiFileAuthState, DisconnectReason } from '@whiskeysockets/baileys';
import qrcode from 'qrcode-terminal';
import path from 'path';
import { fileURLToPath } from 'url';
import { ObsidianVault } from './obsidian.js';
import { CONFIG } from './config.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AUTH_DIR = path.join(__dirname, 'auth_info');

// Inicializar Obsidian
const vault = new ObsidianVault(CONFIG.obsidianVaultPath);

async function start() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

    const sock = makeWASocket.default
        ? makeWASocket.default({ auth: state, printQRInTerminal: false })
        : makeWASocket({ auth: state, printQRInTerminal: false });

    sock.ev.on('creds.update', saveCreds);

    // ─── CONEXION ──────────────────────────────────────────
    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n========================================');
            console.log('  ESCANEA CON TU TELEFONO');
            console.log('  WhatsApp > Dispositivos vinculados');
            console.log('========================================\n');
            qrcode.generate(qr, { small: true });
        }

        if (connection === 'open') {
            console.log('\n[ClowBot] Conectado a WhatsApp!');
            console.log(`[ClowBot] Vault Obsidian: ${CONFIG.obsidianVaultPath}`);
            console.log('[ClowBot] Esperando mensajes en grupos...\n');
        }

        if (connection === 'close') {
            const reason = lastDisconnect?.error?.output?.statusCode;
            if (reason !== DisconnectReason.loggedOut) {
                console.log('[ClowBot] Reconectando...');
                setTimeout(start, 3000);
            } else {
                console.log('[ClowBot] Sesion cerrada. Elimina auth_info/ y vuelve a ejecutar.');
            }
        }
    });

    // ─── ESCUCHAR MENSAJES ─────────────────────────────────
    sock.ev.on('messages.upsert', async ({ messages }) => {
        for (const msg of messages) {
            if (!msg.message || msg.key.fromMe) continue;

            const text = msg.message.conversation
                || msg.message.extendedTextMessage?.text
                || '';

            if (!text.startsWith('!')) continue;

            const chatId = msg.key.remoteJid;
            const isGroup = chatId.endsWith('@g.us');

            // Si hay grupos configurados, solo responder en esos
            if (CONFIG.allowedGroups.length > 0 && isGroup) {
                if (!CONFIG.allowedGroups.includes(chatId)) continue;
            }

            // Permitir mensajes privados si esta habilitado
            if (!isGroup && !CONFIG.allowPrivateMessages) continue;

            console.log(`[Msg] ${isGroup ? 'Grupo' : 'Privado'}: ${text}`);

            try {
                const reply = await handleCommand(text);
                if (reply) {
                    await sock.sendMessage(chatId, { text: reply });
                }
            } catch (err) {
                console.error('[Error]', err.message);
                await sock.sendMessage(chatId, { text: 'Error procesando el comando.' });
            }
        }
    });
}

// ─── COMANDOS ──────────────────────────────────────────────

async function handleCommand(text) {
    const parts = text.trim().split(/\s+/);
    const cmd = parts[0].toLowerCase();

    switch (cmd) {
        case '!agenda':
            return cmdAgenda(parts.slice(1));

        case '!semana':
            return cmdSemana();

        case '!agregar':
        case '!add':
            return cmdAgregar(parts.slice(1));

        case '!listo':
        case '!done':
            return cmdListo(parts.slice(1));

        case '!nota':
        case '!note':
            return cmdNota(text.substring(cmd.length).trim());

        case '!ayuda':
        case '!help':
            return cmdAyuda();

        default:
            return null; // Ignorar comandos desconocidos
    }
}

// ─── !agenda [fecha] ───────────────────────────────────────

function cmdAgenda(args) {
    const dateText = args.join(' ') || 'hoy';
    const date = vault.parseDate(dateText);
    const events = vault.getEvents(date);
    const dateStr = vault.formatDate(date);
    const dayName = vault.getDayName(date);

    if (events.length === 0) {
        return `📋 *${dayName} ${dateStr}*\n\nNo hay compromisos agendados.`;
    }

    let msg = `📋 *Agenda ${dayName} ${dateStr}*\n\n`;
    events.forEach((e, i) => {
        const check = e.done ? '✅' : '⬜';
        msg += `${check} ${i + 1}. *${e.time}* — ${e.description}\n`;
    });

    return msg;
}

// ─── !semana ───────────────────────────────────────────────

function cmdSemana() {
    const week = vault.getWeekEvents();

    if (week.length === 0) {
        return '📅 *Esta semana*\n\nNo hay compromisos agendados.';
    }

    let msg = '📅 *Proximos 7 dias*\n\n';
    for (const day of week) {
        msg += `*${day.day} ${day.date}*\n`;
        for (const e of day.events) {
            const check = e.done ? '✅' : '⬜';
            msg += `  ${check} ${e.time} — ${e.description}\n`;
        }
        msg += '\n';
    }

    return msg;
}

// ─── !agregar <fecha> <hora> <descripcion> ─────────────────

function cmdAgregar(args) {
    if (args.length < 3) {
        return '❌ Formato: *!agregar <fecha> <hora> <descripcion>*\n\n'
            + 'Ejemplos:\n'
            + '• !agregar hoy 14:00 Clase de matematicas\n'
            + '• !agregar manana 09:00 Entrega de proyecto #tarea\n'
            + '• !agregar lunes 08:00 Examen de fisica #examen\n'
            + '• !agregar 15/04 16:00 Reunion de padres';
    }

    const dateText = args[0];
    const time = args[1];
    const description = args.slice(2).join(' ');

    // Extraer categoria si hay hashtag
    let category = 'general';
    const hashMatch = description.match(/#(\w+)/);
    if (hashMatch) {
        category = hashMatch[1];
    }
    const cleanDesc = description.replace(/#\w+/g, '').trim();

    const date = vault.parseDate(dateText);
    const result = vault.addEvent(date, time, cleanDesc, category);

    return `✅ *Compromiso agregado*\n\n`
        + `📅 ${vault.getDayName(date)} ${result.dateStr}\n`
        + `⏰ ${result.timeStr}\n`
        + `📝 ${cleanDesc}\n`
        + `🏷️ ${category}`;
}

// ─── !listo <numero> [fecha] ───────────────────────────────

function cmdListo(args) {
    if (args.length < 1) {
        return '❌ Formato: *!listo <numero>* [fecha]\n\nEjemplo: !listo 1';
    }

    const index = parseInt(args[0]) - 1;
    const dateText = args[1] || 'hoy';
    const date = vault.parseDate(dateText);

    if (vault.completeEvent(date, index)) {
        return `✅ Compromiso #${index + 1} marcado como completado!`;
    } else {
        return `❌ No se encontro el compromiso #${index + 1} para ${vault.formatDate(date)}`;
    }
}

// ─── !nota <titulo> | <contenido> ──────────────────────────

function cmdNota(text) {
    if (!text) {
        return '❌ Formato: *!nota <titulo> | <contenido>*\n\nEjemplo: !nota Ideas proyecto | Usar React para el frontend';
    }

    let title, content;
    if (text.includes('|')) {
        [title, ...content] = text.split('|');
        title = title.trim();
        content = content.join('|').trim();
    } else {
        title = text.substring(0, 50);
        content = text;
    }

    const filePath = vault.addNote(title, content);
    return `📝 *Nota guardada en Obsidian*\n\nTitulo: ${title}\nArchivo: ${path.basename(filePath)}`;
}

// ─── !ayuda ────────────────────────────────────────────────

function cmdAyuda() {
    return `🤖 *ClowBot — Comandos*\n\n`
        + `📋 *!agenda* [fecha] — Ver compromisos\n`
        + `   _!agenda hoy / manana / lunes / 15/04_\n\n`
        + `📅 *!semana* — Ver proximos 7 dias\n\n`
        + `➕ *!agregar* <fecha> <hora> <desc> — Nuevo compromiso\n`
        + `   _!agregar manana 09:00 Examen de mate #examen_\n\n`
        + `✅ *!listo* <num> — Marcar como hecho\n`
        + `   _!listo 1_\n\n`
        + `📝 *!nota* <titulo> | <texto> — Guardar nota\n`
        + `   _!nota Ideas | Usar React para el proyecto_\n\n`
        + `❓ *!ayuda* — Este mensaje\n\n`
        + `_Los datos se guardan en tu vault de Obsidian_`;
}

// ─── INICIAR ───────────────────────────────────────────────

console.log('╔══════════════════════════════════════╗');
console.log('║   ClowBot — Agenda Escolar + Obsidian ║');
console.log('╚══════════════════════════════════════╝\n');

start().catch(console.error);
