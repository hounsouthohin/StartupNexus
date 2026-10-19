'use client';
import { MonProfil, useRole } from '@/components/pieces';
import { PROFILS } from '@/lib/droits';

// « Mon profil » : celui du rôle connecté (un profil par rôle — répétition temps 2).
export default function Page() {
    const role = useRole();
    const profil = PROFILS.find((p) => p.role === role);
    if (!profil) return <p className="text-slate-500">Votre rôle n&apos;a pas de profil.</p>;
    return <MonProfil fiche={profil.fiche} />;
}
