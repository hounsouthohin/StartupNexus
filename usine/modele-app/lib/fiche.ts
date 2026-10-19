// La forme d'une fiche dans la NOTICE (lib/notice.ts, produite par l'usine). Les noms de champs sont
// typés par les types que ZenStack génère : un champ renommé dans le schéma est signalé à la
// compilation (étude 06).

export type Saisie = 'texte' | 'texte_long' | 'nombre' | 'montant' | 'date' | 'date_heure' | 'oui_non'
    | 'email' | 'telephone' | 'url' | 'choix';

// options (champ « choix ») : code enregistré → libellé affiché
type Champ<T> = { nom: Extract<keyof T, string>; libelle: string; type?: 'date' | 'date_heure' | 'etat' | 'oui_non' | 'montant' | 'choix'; options?: Record<string, string> };
type ChampModifiable<T> = { nom: Extract<keyof T, string>; libelle: string; saisie: Saisie; obligatoire: boolean; options?: Record<string, string> };
// fk / cible / proprietaire : pour les listes de choix des formulaires (N1.2) ; le lien vers le profil
// du propriétaire est posé automatiquement, jamais choisi
export type Lien = { nom: string; affiche: string; libelle: string; fk: string; cible: string; proprietaire: boolean; parent?: boolean };

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
    creation?: { libelle: string };       // (N1.2) le bouton du formulaire de création
    designee_par?: { relation: string; libelle: string; libelle_un: string }[];   // (N1.2) qui peut la désigner (intégrité)
    parent?: { fiche: string; fk: string };                                          // (N1.3) une ligne : son parent
    enfants?: { fiche: string; fk: string; libelle: string; libelle_un: string }[];  // (N1.3) les lignes de cette fiche
};
