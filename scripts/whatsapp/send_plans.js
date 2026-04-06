import makeWASocket, { useMultiFileAuthState, DisconnectReason } from '@whiskeysockets/baileys';
import qrcode from 'qrcode-terminal';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AUTH_DIR = path.join(__dirname, 'auth_info');
const DXF_DIR = path.resolve(__dirname, '../../skills/dxf-architect');

async function start() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

    const sock = makeWASocket.default
        ? makeWASocket.default({ auth: state, printQRInTerminal: false })
        : makeWASocket({ auth: state, printQRInTerminal: false });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n=== ESCANEA ESTE CODIGO QR CON TU TELEFONO ===');
            console.log('WhatsApp > Dispositivos vinculados > Vincular dispositivo\n');
            qrcode.generate(qr, { small: true });
        }

        if (connection === 'open') {
            console.log('\n Conectado a WhatsApp!\n');

            const myNumber = sock.user.id.split(':')[0] + '@s.whatsapp.net';
            console.log(`Tu numero: ${sock.user.id}`);

            // Enviar PNGs como imagenes
            const pngFiles = [
                'villa_moderna_planta_baja.png',
                'villa_moderna_planta_alta.png',
            ];

            for (const file of pngFiles) {
                const filepath = path.join(DXF_DIR, file);
                if (fs.existsSync(filepath)) {
                    const buffer = fs.readFileSync(filepath);
                    await sock.sendMessage(myNumber, {
                        image: buffer,
                        caption: file.replace('.png', '').replace(/_/g, ' ').toUpperCase(),
                    });
                    console.log(`Enviado: ${file}`);
                }
            }

            // Enviar DXFs como documentos
            const dxfFiles = [
                'villa_moderna_planta_baja.dxf',
                'villa_moderna_planta_alta.dxf',
            ];

            for (const file of dxfFiles) {
                const filepath = path.join(DXF_DIR, file);
                if (fs.existsSync(filepath)) {
                    const buffer = fs.readFileSync(filepath);
                    await sock.sendMessage(myNumber, {
                        document: buffer,
                        mimetype: 'application/dxf',
                        fileName: file,
                    });
                    console.log(`Enviado: ${file}`);
                }
            }

            console.log('\nTodos los archivos enviados!');
            process.exit(0);
        }

        if (connection === 'close') {
            const reason = lastDisconnect?.error?.output?.statusCode;
            if (reason !== DisconnectReason.loggedOut) {
                console.log('Reconectando...');
                start();
            } else {
                console.log('Sesion cerrada.');
                process.exit(1);
            }
        }
    });
}

start().catch(console.error);
