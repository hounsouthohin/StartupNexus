import { Suspense } from 'react';
import { Entete } from '@/components/entete';
import { Fournisseur } from '@/components/pieces';
import { ensureProfile, getUser } from '@/lib/session';
import type { Role } from '@/lib/droits';

// Next.js 16 (« cache des composants ») : ce qui lit la session est derrière un <Suspense>.
export default function LayoutApp({ children }: { children: React.ReactNode }) {
    return (
        <Suspense fallback={<p className="p-6">Chargement…</p>}>
            <AvecSession>{children}</AvecSession>
        </Suspense>
    );
}

async function AvecSession({ children }: { children: React.ReactNode }) {
    const user = await getUser();
    await ensureProfile(user);
    const role = (user?.role ?? 'visitor') as Role;
    return (
        <Fournisseur role={role}>
            <Entete role={role} />
            <main className="mx-auto max-w-4xl p-6">{children}</main>
        </Fournisseur>
    );
}
