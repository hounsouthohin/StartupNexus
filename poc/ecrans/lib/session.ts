import 'server-only';
import { cookies } from 'next/headers';
import { dbFor, type User } from './db';

// E6 : connexion SIMULÉE par un cookie (Clerk n'est pas ce qu'on compare ; validé par la PoC).
// Valeur du cookie : « <id>:<rôle> », par exemple « adherent_1:adherent ».
export async function getUser(): Promise<User | null> {
    const raw = (await cookies()).get('poc_user')?.value;
    if (!raw) return null;
    const [id, role] = raw.split(':');
    return role === 'adherent' || role === 'bibliothecaire' ? { id, role } : null;
}

// « Mon profil » créé à la première visite d'un adhérent, par le client AVEC règles.
export async function ensureProfile(user: User | null) {
    if (user?.role !== 'adherent') return;
    const db = dbFor(user);
    if (await db.member.findFirst()) return;
    try {
        await db.member.create({ data: { name: `Adhérent ${user.id}`, email: `${user.id}@exemple.fr` } });
    } catch {
        // deux requêtes simultanées : l'autre l'a créé
    }
}
