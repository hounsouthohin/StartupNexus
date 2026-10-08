// Ce que l'ÉCRAN a le droit d'afficher, lu dans lib/droits.ts (produit par l'usine depuis la
// matrice). Il ne protège rien : le serveur refuse de toute façon. Il évite d'afficher un bouton
// que le serveur refuserait (affordance honnête).
import { MATRICE, type Role } from './droits';
import type { NomFiche } from './notice';

export type Droits = { voir?: boolean; creer?: boolean; modifier?: boolean; transitions?: Record<string, string[]> };
export type Action = 'voir' | 'creer' | 'modifier' | `etat:${string}`;

export function peut(role: Role, fiche: NomFiche, action: Action, etatActuel?: string): boolean {
    const d = MATRICE[role]?.[fiche];
    if (!d) return false;
    if (action.startsWith('etat:')) return !!etatActuel && !!d.transitions?.[etatActuel]?.includes(action.slice(5));
    return !!d[action as 'voir' | 'creer' | 'modifier'];
}
