// La forme d'une fiche dans la NOTICE (lib/notice.ts, produite par l'usine). Les noms de champs sont
// typés par les types que ZenStack génère : un champ renommé dans le schéma est signalé à la
// compilation (étude 06).

export type Saisie = 'texte' | 'texte_long' | 'nombre' | 'montant' | 'date' | 'date_heure' | 'oui_non'
    | 'email' | 'telephone' | 'url' | 'choix';

// options (champ « choix ») : code enregistré → libellé affiché
type Champ<T> = { nom: Extract<keyof T, string>; libelle: string; type?: 'date' | 'date_heure' | 'etat' | 'oui_non' | 'montant' | 'choix'; options?: Record<string, string> };
type ChampModifiable<T> = { nom: Extract<keyof T, string>; libelle: string; saisie: Saisie; obligatoire: boolean; options?: Record<string, string> };
export type Lien = { nom: string; affiche: string; libelle: string };

export type Fiche<T = Record<string, unknown>> = {
    modele: string;
    libelle: string;
    titre: string;
    champs: Champ<T>[];
    modifiables: ChampModifiable<T>[];
    liens?: Lien[];
    tri?: { champ: Extract<keyof T, string>; sens: 'asc' | 'desc' };
    etat?: { champ: Extract<keyof T, string>; initial: string; libelles: Record<string, string>; boutons: Record<string, string> };
    actionsLigne?: { libelle: string; cree: string; lien: string }[];
};
