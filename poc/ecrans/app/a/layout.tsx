import { Suspense } from 'react';
import { ProviderA } from '@/components/a/pieces';
import { Entete } from '@/components/entete';
import { ensureProfile, getUser } from '@/lib/session';

// Next.js 16 (« cache des composants ») : ce qui lit la session est placé derrière un <Suspense>
// (patron du guide officiel « authentication with cache components »).
export default function LayoutA({ children }: { children: React.ReactNode }) {
    return (
        <Suspense fallback={<p className="p-6">Chargement…</p>}>
            <AvecSession>{children}</AvecSession>
        </Suspense>
    );
}

async function AvecSession({ children }: { children: React.ReactNode }) {
    const user = await getUser();
    await ensureProfile(user);
    const role = user?.role ?? 'visitor';
    return (
        <ProviderA role={role}>
            <Entete role={role} prefixe="/a" variante="A · Refine" />
            <main className="mx-auto max-w-4xl p-6">{children}</main>
        </ProviderA>
    );
}
