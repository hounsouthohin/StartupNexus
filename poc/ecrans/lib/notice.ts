// La NOTICE : ce que les pièces génériques savent de chaque fiche. Partagée par les deux variantes.
// Les noms de champs sont TYPÉS par les types que ZenStack génère depuis le schéma : si un champ
// est renommé dans le schéma, la compilation signale la notice (vérifié dans l'étude 06).
import type { Book, Borrowing, Member } from '@/zenstack/models';

export type Role = 'visitor' | 'adherent' | 'bibliothecaire';
export type NomFiche = 'Book' | 'Borrowing' | 'Member';

type Champ<T> = { nom: Extract<keyof T, string>; libelle: string; type?: 'date' | 'etat' };
export type Lien = { nom: string; affiche: string; libelle: string }; // relation affichée dans la fiche
export type Fiche<T = Record<string, unknown>> = {
    modele: 'book' | 'borrowing' | 'member'; // nom côté API ZenStack
    libelle: string;
    titre: string;
    champs: Champ<T>[];
    modifiables?: Champ<T>[];
    liens?: Lien[];
    tri?: { champ: Extract<keyof T, string>; sens: 'asc' | 'desc' };
    etat?: { champ: Extract<keyof T, string>; libelles: Record<string, string>; boutons: Record<string, string> };
    actionsLigne?: { libelle: string; cree: NomFiche; lien: string }[]; // « Emprunter » crée un emprunt lié
};

const book = {
    modele: 'book',
    libelle: 'ouvrage',
    titre: 'Catalogue des ouvrages',
    champs: [
        { nom: 'title', libelle: 'Titre' },
        { nom: 'author', libelle: 'Auteur' },
    ],
    tri: { champ: 'title', sens: 'asc' },
    actionsLigne: [{ libelle: 'Emprunter', cree: 'Borrowing', lien: 'bookId' }],
} satisfies Fiche<Book>;

const borrowing = {
    modele: 'borrowing',
    libelle: 'emprunt',
    titre: 'Emprunts',
    champs: [
        { nom: 'status', libelle: 'État', type: 'etat' },
        { nom: 'createdAt', libelle: 'Demandé le', type: 'date' },
    ],
    liens: [
        { nom: 'book', affiche: 'title', libelle: 'Ouvrage' },
        { nom: 'member', affiche: 'name', libelle: 'Adhérent' },
    ],
    tri: { champ: 'createdAt', sens: 'desc' },
    etat: {
        champ: 'status',
        libelles: { requested: 'demandé', accepted: 'accepté', refused: 'refusé', returned: 'rendu' },
        boutons: { accepted: 'Accepter', refused: 'Refuser', returned: 'Marquer rendu' },
    },
} satisfies Fiche<Borrowing>;

const member = {
    modele: 'member',
    libelle: 'profil',
    titre: 'Mon profil',
    champs: [
        { nom: 'name', libelle: 'Nom' },
        { nom: 'email', libelle: 'E-mail' },
        { nom: 'phone', libelle: 'Téléphone' },
    ],
    modifiables: [
        { nom: 'name', libelle: 'Nom' },
        { nom: 'phone', libelle: 'Téléphone' },
    ],
} satisfies Fiche<Member>;

export const NOTICE: Record<NomFiche, Fiche> = { Book: book, Borrowing: borrowing, Member: member } as Record<NomFiche, Fiche>;
