/**
 * Configuracion de ClowBot
 *
 * INSTRUCCIONES:
 * 1. Cambia obsidianVaultPath a la ruta de TU vault de Obsidian
 * 2. Para limitar a ciertos grupos, agrega sus IDs a allowedGroups
 *    (dejalo vacio para responder en todos los grupos)
 * 3. allowPrivateMessages: true si quieres que responda en chat privado
 */

export const CONFIG = {
    // ─── Ruta al vault de Obsidian ─────────────────────────
    // Windows: 'C:\\Users\\TuNombre\\Documents\\Obsidian\\MiVault'
    // Mac:     '/Users/tunombre/Documents/Obsidian/MiVault'
    // Linux:   '/home/tunombre/Documents/Obsidian/MiVault'
    obsidianVaultPath: './obsidian-vault',

    // ─── Grupos permitidos ─────────────────────────────────
    // Deja vacio [] para responder en TODOS los grupos
    // Para obtener el ID de un grupo, envia "!id" en el grupo
    // Ejemplo: ['120363012345678@g.us']
    allowedGroups: [],

    // ─── Mensajes privados ─────────────────────────────────
    allowPrivateMessages: true,
};
