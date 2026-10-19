// NOYAU des tests d'écran — ce que tous les blocs partagent : la matrice d'origine (les ATTENTES), la
// connexion simulée, l'ordre de création, et quelques gestes communs. Les attentes viennent de
// verification/matrice.json, PAS de lib/droits.ts que lisent les écrans : si le traducteur se trompait
// dans les droits, l'écran et le test ne se tromperaient pas ensemble — le test échoue. Notice et menu ne
// servent qu'à trouver libellés et chemins. (N1.3) découpé en noyau + un module par bloc (e2e/blocs/),
// comme le testeur des règles (verification/noyau.mts + verification/blocs/).
import { expect, type BrowserContext, type Locator, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { NOTICE, type NomFiche } from '../lib/notice';

export type Cellule = {
    actor: string; entity: string; see: string; create: string; create_while?: string[]; transitions: Record<string, string[]>;
    edit: boolean; edit_while: string[]; delete: boolean; delete_while: string[];
};
export const cellules: Cellule[] = JSON.parse(readFileSync(resolve('verification/matrice.json'), 'utf8')).cells;
export type Action = 'voir' | 'creer' | 'modifier' | 'supprimer' | `etat:${string}`;

export function attendu(role: string, fiche: string, action: Action, etat?: string): boolean {
    const c = cellules.find((x) => x.actor === role && x.entity === fiche);
    if (!c) return false;
    if (action === 'voir') return c.see !== 'none';
    if (action === 'creer') return c.create === 'yes';
    if (action === 'modifier') return c.edit && (!c.edit_while?.length || (!!etat && c.edit_while.includes(etat)));
    if (action === 'supprimer') return c.delete && (!c.delete_while?.length || (!!etat && c.delete_while.includes(etat)));
    return !!etat && !!c.transitions[etat]?.includes(action.slice(5));
}

const BASE = process.env.BASE_URL ?? 'http://localhost:3300';
export const roles = [...new Set(cellules.map((c) => c.actor))];
export const connectes = roles.filter((r) => r !== 'visitor');
export const seConnecter = (context: BrowserContext, role: string) =>
    role === 'visitor' ? Promise.resolve() : context.addCookies([{ name: 'session_usine', value: `${role}_1:${role}`, url: BASE }]);
export type Notice = (typeof NOTICE)[NomFiche];
// (N1.3) les LIGNES (fiches enfants) vivent dans la page de leur parent : seul le bloc « enfants » les juge ;
// les autres blocs ne voient que les fiches qui ont leur propre page
export const toutes = Object.entries(NOTICE) as [NomFiche, Notice][];
export const fiches = toutes.filter(([, f]) => !f.parent);
export const fichesDeLaMatrice = [...new Set(cellules.map((c) => c.entity))].filter((e) => !NOTICE[e as NomFiche]?.parent);
// l'ordre de création (les fiches désignées d'abord) : celui des données de départ
const ordre: string[] = JSON.parse(readFileSync(resolve('depart.json'), 'utf8')).creation;
export const parOrdre = [...fiches].sort(([, a], [, b]) => ordre.indexOf(a.modele) - ordre.indexOf(b.modele));
// (13 oct) les lignes aussi, dans l'ordre de création : une ligne qui désigne une autre ligne (le point de checklist
// d'un type d'intervention) n'est essayée qu'après elle — sinon il n'y avait rien à choisir (portes, lecture Claude)
export const toutesParOrdre = [...toutes].sort(([, a], [, b]) => ordre.indexOf(a.modele) - ordre.indexOf(b.modele));

// la fiche la plus récente d'une liste (tri par date décroissante pour les fiches à circuit)
export async function ouvrirPlusRecente(page: Page, nom: NomFiche) {
    await page.goto(`/f/${nom}`);
    await expect(page.locator('main h1')).toBeVisible();
    await page.locator('main li a').first().click();
    await expect(page.locator('dl')).toBeVisible();
}
// (n° 55) la valeur du champ « État » d'une fiche ouverte — et lui seul : chercher le libellé dans n'importe quel
// champ trouvait aussi « Réparations à effectuer » pour l'état « à effectuer » (garage), et pouvait conclure à tort
export const champEtat = (page: Page) => page.locator('dt', { hasText: /^État$/ }).locator('xpath=following-sibling::dd[1]');
// l'état affiché d'une fiche (code), lu à l'écran
export async function etatAffiche(page: Page, nom: NomFiche): Promise<string | undefined> {
    const etat = NOTICE[nom].etat;
    if (!etat) return undefined;
    const libelle = (await champEtat(page).innerText()).trim();
    return Object.entries(etat.libelles).find(([, l]) => l === libelle)?.[0];
}

const VALEUR: Record<string, string> = { texte: 'Essai', texte_long: 'Essai long', nombre: '3', montant: '12.50',
    date: '2026-03-15', date_heure: '2026-03-15T10:30', email: 'essai@exemple.invalid', telephone: '0600000000',
    url: 'https://exemple.invalid' };
// Remplit et envoie le formulaire de création (le 1er champ texte reçoit `marque` si elle est donnée) ;
// false si une fiche liée à choisir manque (aucune visible) — on attend la fin du chargement des listes
// de choix avant de le dire (sinon on le constatait trop tôt, ou trop tard).
export async function creerParFormulaire(page: Page, nom: NomFiche, marque?: string): Promise<boolean> {
    const fiche = NOTICE[nom];
    await page.getByRole('button', { name: fiche.creation!.libelle, exact: true }).click();
    const form = page.locator('main form');
    await expect(form).toBeVisible();
    await expect(form.getByText('Chargement…')).toHaveCount(0);
    if ((await form.getByText(/à choisir\.$/).count()) > 0) return false;
    let marquee = false;
    for (const c of fiche.modifiables) {
        const champ = form.locator(`[name="${c.nom}"]`);
        if (c.saisie === 'oui_non') await champ.check();
        else if (c.saisie !== 'choix') {
            const v = marque && c.saisie === 'texte' && !marquee ? marque : `${VALEUR[c.saisie]}${c.saisie.startsWith('texte') ? ` ${c.libelle}` : ''}`;
            marquee ||= !!marque && c.saisie === 'texte';
            await champ.fill(v);
        }
    }
    await form.getByRole('button', { name: 'Créer' }).click();
    await expect(page.getByText('Enregistré.')).toBeVisible();
    return true;
}

// la section des LIGNES d'une fiche enfant, dans la page (ouverte) de son parent
export const sectionLignes = (page: Page, nom: NomFiche) => page.locator(`[data-bloc="lignes"][data-fiche="${nom}"]`);
const VALEUR_LIGNE: Record<string, string> = { texte: 'Ligne', texte_long: 'Ligne longue', nombre: '2', montant: '7.50',
    date: '2026-04-01', date_heure: '2026-04-01T09:00', email: 'ligne@exemple.invalid', telephone: '0611111111',
    url: 'https://exemple.invalid/ligne' };
// (n° 54) Ajoute une ligne par le formulaire de sa section (le 1er champ texte reçoit `marque`) ; null si une fiche
// liée à choisir manque, sinon si la ligne porte la marque. Partagé par les blocs « créer » et « enfants ».
export async function ajouterLigneParFormulaire(section: Locator, nom: NomFiche, marque: string): Promise<boolean | null> {
    const fiche = NOTICE[nom];
    await section.getByRole('button', { name: `Ajouter : ${fiche.libelle}`, exact: true }).click();
    const form = section.locator('form');
    await expect(form).toBeVisible();
    await expect(form.getByText('Chargement…')).toHaveCount(0);
    if ((await form.getByText(/à choisir\.$/).count()) > 0) return null;
    let marquee = false;
    for (const ch of fiche.modifiables) {
        const champ = form.locator(`[name="${ch.nom}"]`);
        if (ch.saisie === 'oui_non') await champ.check();
        else if (ch.saisie !== 'choix') {
            await champ.fill(ch.saisie === 'texte' && !marquee ? marque : VALEUR_LIGNE[ch.saisie]);
            marquee ||= ch.saisie === 'texte';
        }
    }
    await form.getByRole('button', { name: 'Ajouter', exact: true }).click();
    return marquee;
}
