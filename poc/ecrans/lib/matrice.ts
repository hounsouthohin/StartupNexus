// Les droits tels que l'ÉCRAN les lit (recopiés de la matrice de référence ; dans l'usine, produits
// par le calculateur). Ils ne protègent rien : le serveur refuse de toute façon. Ils évitent
// d'afficher un bouton que le serveur refuserait. Partagés par les deux variantes.
import type { NomFiche, Role } from './notice';

type Droits = { voir?: boolean; creer?: boolean; modifier?: boolean; transitions?: Record<string, string[]> };

const MATRICE: Record<Role, Partial<Record<NomFiche, Droits>>> = {
    visitor: { Book: { voir: true } },
    adherent: { Book: { voir: true }, Borrowing: { voir: true, creer: true }, Member: { voir: true, modifier: true } },
    bibliothecaire: {
        Book: { voir: true },
        Borrowing: { voir: true, transitions: { requested: ['accepted', 'refused'], accepted: ['returned'] } },
    },
};

export type Action = 'voir' | 'creer' | 'modifier' | `etat:${string}`;

export function peut(role: Role, fiche: NomFiche, action: Action, etatActuel?: string): boolean {
    const d = MATRICE[role][fiche];
    if (!d) return false;
    if (action.startsWith('etat:')) return !!etatActuel && !!d.transitions?.[etatActuel]?.includes(action.slice(5));
    return !!d[action as 'voir' | 'creer' | 'modifier'];
}

export const MENU: { fiche: NomFiche; chemin: string; libelle: string; action: Action }[] = [
    { fiche: 'Book', chemin: 'catalogue', libelle: 'Catalogue', action: 'voir' },
    { fiche: 'Borrowing', chemin: 'emprunts', libelle: 'Emprunts', action: 'voir' },
    { fiche: 'Member', chemin: 'profil', libelle: 'Mon profil', action: 'modifier' },
];
