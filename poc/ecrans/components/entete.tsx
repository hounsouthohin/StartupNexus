// En-tête commun : menu par rôle (lu dans la matrice) et rôle simulé. Identique pour A et B.
import Link from 'next/link';
import { MENU, peut } from '@/lib/matrice';
import type { Role } from '@/lib/notice';

const NOM = { visitor: 'visiteur', adherent: 'adhérent', bibliothecaire: 'bibliothécaire' } as const;

export function Entete({ role, prefixe, variante }: { role: Role; prefixe: string; variante: string }) {
    return (
        <header className="flex items-center gap-6 border-b bg-white px-6 py-3">
            <span className="font-semibold">📚 Médiathèque · {variante}</span>
            <nav className="flex gap-4 text-sm">
                {MENU.filter((m) => peut(role, m.fiche, m.action)).map((m) => (
                    <Link key={m.chemin} href={`${prefixe}/${m.chemin}`} className="hover:underline">{m.libelle}</Link>
                ))}
            </nav>
            <span className="ml-auto rounded bg-slate-100 px-2 py-1 text-xs">connecté en : <b>{NOM[role]}</b></span>
        </header>
    );
}
