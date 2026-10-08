// En-tête : le menu par rôle (lu dans les droits produits par l'usine) et le rôle connecté.
import Link from 'next/link';
import { MENU, TITRE, type Role } from '@/lib/droits';
import { peut } from '@/lib/peut';

export function Entete({ role }: { role: Role }) {
    return (
        <header className="flex items-center gap-6 border-b bg-white px-6 py-3">
            <Link href="/" className="font-semibold">{TITRE}</Link>
            <nav className="flex gap-4 text-sm">
                {MENU.filter((m) => peut(role, m.fiche, m.action)).map((m) => (
                    <Link key={m.chemin} href={m.chemin} className="hover:underline">{m.libelle}</Link>
                ))}
            </nav>
            <span className="ml-auto rounded bg-slate-100 px-2 py-1 text-xs">
                connecté en : <b>{role === 'visitor' ? 'visiteur' : role}</b>
            </span>
        </header>
    );
}
