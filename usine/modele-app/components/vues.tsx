'use client';
// AFFICHAGE pur : il reçoit des données, il n'en cherche aucune (étude 06).
import Link from 'next/link';
import type { Fiche, Saisie } from '@/lib/fiche';

type Ligne = Record<string, unknown> & { id: string };

export function valeur(fiche: Fiche, ligne: Ligne, nom: string, type?: string): string {
    const v = ligne[nom];
    if (v == null || v === '') return '—';
    if (type === 'date') return new Date(String(v)).toLocaleString('fr-FR');
    if (type === 'etat') return fiche.etat?.libelles[String(v)] ?? String(v);
    if (type === 'oui_non') return v ? 'oui' : 'non';
    return String(v);
}

function valeurLien(ligne: Ligne, nom: string, affiche: string): string {
    const lie = ligne[nom] as Record<string, unknown> | null | undefined;
    return lie ? String(lie[affiche] ?? '') : '';
}

export function Tableau(props: { fiche: Fiche; lignes: Ligne[]; lienDetail?: string; actions?: (l: Ligne) => React.ReactNode }) {
    const { fiche, lignes } = props;
    if (!lignes.length) return <p className="text-slate-500">Aucun élément.</p>;
    return (
        <ul className="divide-y rounded border bg-white">
            {lignes.map((l) => {
                const morceaux = [...(fiche.liens ?? []).map((k) => valeurLien(l, k.nom, k.affiche)),
                    ...fiche.champs.map((c) => valeur(fiche, l, c.nom, c.type))].filter((x) => x && x !== '—');
                return (
                    <li key={l.id} className="flex items-center justify-between gap-4 p-3">
                        <span>
                            {morceaux.map((x, i) => (i === 0 && props.lienDetail ? (
                                <Link key={i} href={`${props.lienDetail}/${l.id}`} className="font-semibold hover:underline">{x}</Link>
                            ) : (
                                <span key={i} className={i === 0 ? 'font-semibold' : 'text-slate-500'}>{i ? ' — ' : ''}{x}</span>
                            )))}
                        </span>
                        {props.actions?.(l)}
                    </li>
                );
            })}
        </ul>
    );
}

export function Details({ fiche, ligne }: { fiche: Fiche; ligne: Ligne }) {
    return (
        <dl className="grid grid-cols-[10rem_1fr] gap-2 rounded border bg-white p-4 text-sm">
            {(fiche.liens ?? []).map((k) => (
                <Paire key={k.nom} libelle={k.libelle} valeur={valeurLien(ligne, k.nom, k.affiche) || '—'} />
            ))}
            {fiche.champs.map((c) => <Paire key={c.nom} libelle={c.libelle} valeur={valeur(fiche, ligne, c.nom, c.type)} />)}
        </dl>
    );
}

function Paire({ libelle, valeur }: { libelle: string; valeur: string }) {
    return (
        <>
            <dt className="text-slate-500">{libelle}</dt>
            <dd>{valeur}</dd>
        </>
    );
}

export function Bouton(props: { onClick: () => void; children: React.ReactNode; disabled?: boolean }) {
    return (
        <button disabled={props.disabled} onClick={props.onClick}
            className="rounded bg-slate-900 px-3 py-1 text-sm text-white disabled:opacity-50">{props.children}</button>
    );
}

const ENTREE: Record<Saisie, string> = { texte: 'text', texte_long: 'text', nombre: 'number', date: 'date',
    date_heure: 'datetime-local', oui_non: 'checkbox', email: 'email', telephone: 'tel', url: 'url' };

// Convertit la saisie du navigateur dans le type attendu par le schéma.
function lire(saisie: Saisie, brut: FormDataEntryValue | null, obligatoire: boolean): unknown {
    if (saisie === 'oui_non') return brut === 'on';
    const s = typeof brut === 'string' ? brut.trim() : '';
    if (!s) return obligatoire ? '' : null;
    if (saisie === 'nombre') return Number(s);
    if (saisie === 'date' || saisie === 'date_heure') return new Date(s);
    return s;
}

export function Formulaire(props: {
    fiche: Fiche; ligne: Ligne; onSave: (valeurs: Record<string, unknown>) => void;
    etat: 'repos' | 'en-cours' | 'ok' | 'erreur'; erreur?: string;
}) {
    const { fiche, ligne } = props;
    return (
        <form className="space-y-3 rounded border bg-white p-4" onSubmit={(e) => {
            e.preventDefault();
            const data = new FormData(e.currentTarget);
            props.onSave(Object.fromEntries(fiche.modifiables.map((c) => [c.nom, lire(c.saisie, data.get(c.nom), c.obligatoire)])));
        }}>
            {fiche.modifiables.map((c) => (
                <label key={c.nom} className="block text-sm">
                    <span className="text-slate-500">{c.libelle}{c.obligatoire ? '' : ' (facultatif)'}</span>
                    {c.saisie === 'texte_long' ? (
                        <textarea name={c.nom} defaultValue={String(ligne[c.nom] ?? '')} className="mt-1 block w-full rounded border p-2" />
                    ) : c.saisie === 'oui_non' ? (
                        <input type="checkbox" name={c.nom} defaultChecked={!!ligne[c.nom]} className="ml-2" />
                    ) : (
                        <input name={c.nom} type={ENTREE[c.saisie]} required={c.obligatoire}
                            defaultValue={String(ligne[c.nom] ?? '')} className="mt-1 block w-full rounded border p-2" />
                    )}
                </label>
            ))}
            <button disabled={props.etat === 'en-cours'} className="rounded bg-slate-900 px-3 py-1 text-sm text-white">Enregistrer</button>
            {props.etat === 'ok' && <span className="ml-3 text-sm text-green-700">Enregistré.</span>}
            {props.etat === 'erreur' && <span className="ml-3 text-sm text-red-700">Refusé : {props.erreur}</span>}
        </form>
    );
}
