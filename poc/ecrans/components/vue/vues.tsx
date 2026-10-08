'use client';
// AFFICHAGE pur, partagé par les deux variantes : il reçoit des données, il n'en cherche aucune.
import Link from 'next/link';
import type { Fiche } from '@/lib/notice';

type Ligne = Record<string, unknown> & { id: string };

export function valeur(fiche: Fiche, ligne: Ligne, nom: string, type?: string): string {
    const v = ligne[nom];
    if (v == null) return '—';
    if (type === 'date') return new Date(String(v)).toLocaleString('fr-FR');
    if (type === 'etat') return fiche.etat?.libelles[String(v)] ?? String(v);
    return String(v);
}

export function Tableau(props: {
    fiche: Fiche;
    lignes: Ligne[];
    lienDetail?: string;
    actions?: (ligne: Ligne) => React.ReactNode;
}) {
    const { fiche, lignes } = props;
    if (!lignes.length) return <p className="text-slate-500">Aucun élément.</p>;
    return (
        <ul className="divide-y rounded border bg-white">
            {lignes.map((l) => (
                <li key={l.id} className="flex items-center justify-between gap-4 p-3">
                    <span>
                        {[...(fiche.liens ?? []).map((k) => valeurLien(l, k.nom, k.affiche)),
                          ...fiche.champs.map((c) => valeur(fiche, l, c.nom, c.type))]
                            .filter((x) => x && x !== '—')
                            .map((x, i) => (i === 0 && props.lienDetail ? (
                                <Link key={i} href={`${props.lienDetail}/${l.id}`} className="font-semibold hover:underline">{x}</Link>
                            ) : (
                                <span key={i} className={i === 0 ? 'font-semibold' : 'text-slate-500'}>{i ? ' — ' : ''}{x}</span>
                            )))}
                    </span>
                    {props.actions?.(l)}
                </li>
            ))}
        </ul>
    );
}

function valeurLien(ligne: Ligne, nom: string, affiche: string): string {
    const lie = ligne[nom] as Record<string, unknown> | null | undefined;
    return lie ? String(lie[affiche] ?? '') : '';
}

export function Details({ fiche, ligne }: { fiche: Fiche; ligne: Ligne }) {
    return (
        <dl className="grid grid-cols-[10rem_1fr] gap-2 rounded border bg-white p-4 text-sm">
            {(fiche.liens ?? []).map((k) => (
                <Paire key={k.nom} libelle={k.libelle} valeur={valeurLien(ligne, k.nom, k.affiche) || '—'} />
            ))}
            {fiche.champs.map((c) => (
                <Paire key={c.nom} libelle={c.libelle} valeur={valeur(fiche, ligne, c.nom, c.type)} />
            ))}
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
            className="rounded bg-slate-900 px-3 py-1 text-sm text-white disabled:opacity-50">
            {props.children}
        </button>
    );
}

export function Formulaire(props: {
    fiche: Fiche;
    ligne: Ligne;
    onSave: (valeurs: Record<string, string | null>) => void;
    etat: 'repos' | 'en-cours' | 'ok' | 'erreur';
    erreur?: string;
}) {
    const { fiche, ligne } = props;
    return (
        <form className="space-y-3 rounded border bg-white p-4"
            onSubmit={(e) => {
                e.preventDefault();
                const data = new FormData(e.currentTarget);
                props.onSave(Object.fromEntries((fiche.modifiables ?? []).map((c) => [c.nom, (data.get(c.nom) as string) || null])));
            }}>
            {(fiche.modifiables ?? []).map((c) => (
                <label key={c.nom} className="block text-sm">
                    <span className="text-slate-500">{c.libelle}</span>
                    <input name={c.nom} defaultValue={String(ligne[c.nom] ?? '')} className="mt-1 block w-full rounded border p-2" />
                </label>
            ))}
            <button disabled={props.etat === 'en-cours'} className="rounded bg-slate-900 px-3 py-1 text-sm text-white">Enregistrer</button>
            {props.etat === 'ok' && <span className="ml-3 text-sm text-green-700">Enregistré.</span>}
            {props.etat === 'erreur' && <span className="ml-3 text-sm text-red-700">Refusé : {props.erreur}</span>}
        </form>
    );
}
