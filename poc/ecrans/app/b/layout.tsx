import { Suspense } from 'react';
import { ProviderB } from '@/components/b/pieces';
import { Entete } from '@/components/entete';
import { ensureProfile, getUser } from '@/lib/session';

// Next.js 16 (« cache des composants ») : ce qui lit la session est placé derrière un <Suspense>
// (patron du guide officiel « authentication with cache components »).
export default function LayoutB({ children }: { children: React.ReactNode }) {
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
        <ProviderB role={role}>
            <Entete role={role} prefixe="/b" variante="B · nos pièces" />
            <main className="mx-auto max-w-4xl p-6">{children}</main>
        </ProviderB>
    );
}
