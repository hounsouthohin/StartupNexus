'use client';
import { MonProfil } from '@/components/pieces';
import { PROFIL } from '@/lib/droits';

export default function Page() {
    if (!PROFIL) return <p className="text-slate-500">Cette application n&apos;a pas de profil.</p>;
    return <MonProfil fiche={PROFIL.fiche} />;
}
