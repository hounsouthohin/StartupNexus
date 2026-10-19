// Ce que l'ÉCRAN a le droit d'afficher, lu dans lib/droits.ts (produit par l'usine depuis la
// matrice). Il ne protège rien : le serveur refuse de toute façon. Il évite d'afficher un bouton
// que le serveur refuserait (affordance honnête).
import { MATRICE, type Role } from './droits';
import type { NomFiche } from './notice';

export type Droits = {
    voir?: boolean; creer?: boolean; modifier?: boolean; supprimer?: boolean;
    modifier_pendant?: string[]; supprimer_pendant?: string[];      // (N1.2) seulement dans ces états
    creer_pendant?: string[];                                       // (N1.3) une ligne : selon l'état de son parent
    transitions?: Record<string, string[]>;
};
export type Action = 'voir' | 'creer' | 'modifier' | 'supprimer' | `etat:${string}`;

export function peut(role: Role, fiche: NomFiche, action: Action, etatActuel?: string): boolean {
    const d = MATRICE[role]?.[fiche];
    if (!d) return false;
    if (action.startsWith('etat:')) return !!etatActuel && !!d.transitions?.[etatActuel]?.includes(action.slice(5));
    if (action === 'modifier' || action === 'supprimer' || action === 'creer') {
        const pendant = action === 'modifier' ? d.modifier_pendant : action === 'supprimer' ? d.supprimer_pendant : d.creer_pendant;
        return !!d[action] && (!pendant?.length || (!!etatActuel && pendant.includes(etatActuel)));
    }
    return !!d.voir;
}
