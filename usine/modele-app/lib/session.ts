import 'server-only';
import { cookies } from 'next/headers';
import { dbFor, type User } from './db';
import { PROFIL, ROLES_CONNECTES, type Role } from './droits';
import { NOTICE } from './notice';

// Connexion SIMULÉE par un cookie « <id>:<rôle> » (Clerk prendra le relais en N1.5).
export async function getUser(): Promise<User | null> {
    const raw = (await cookies()).get('session_usine')?.value;
    if (!raw) return null;
    const [id, role] = raw.split(':');
    return id && ROLES_CONNECTES.includes(role as Role) ? { id, role } : null;
}

// Valeur provisoire d'un champ obligatoire du profil, à compléter par la personne.
function provisoire({ type, defaut }: { type: string; defaut?: string }, user: User): unknown {
    if (defaut !== undefined) return defaut;          // un choix : sa première valeur
    if (type === 'email') return `${user.id}@exemple.invalid`;
    if (type === 'nombre') return 0;
    if (type === 'montant') return '0';
    if (type === 'oui_non') return false;
    if (type === 'date' || type === 'date_heure') return new Date();
    return 'À compléter';
}

// « Mon profil » est créé à la première visite, par le client AVEC règles.
export async function ensureProfile(user: User | null) {
    if (!PROFIL || user?.role !== PROFIL.role) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const table = (dbFor(user) as any)[NOTICE[PROFIL.fiche].modele];
    if (await table.findFirst()) return;
    try {
        await table.create({ data: Object.fromEntries(PROFIL.obligatoires.map((c) => [c.nom, provisoire(c, user)])) });
    } catch {
        // deux requêtes simultanées : l'autre l'a créé
    }
}
