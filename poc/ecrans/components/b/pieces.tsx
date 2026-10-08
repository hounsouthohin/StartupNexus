'use client';
// VARIANTE B — nos pièces génériques, branchées sur les fonctions que ZenStack génère depuis le
// schéma (@zenstackhq/tanstack-query). Seule la PLOMBERIE est ici ; l'affichage est partagé.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { QuerySettingsProvider, useClientQueries } from '@zenstackhq/tanstack-query/react';
import { createContext, useContext, useState } from 'react';
import { Bouton, Details, Formulaire, Tableau } from '@/components/vue/vues';
import { peut } from '@/lib/matrice';
import { NOTICE, type NomFiche, type Role } from '@/lib/notice';
import { schema } from '@/zenstack/schema';

const RoleB = createContext<Role>('visitor');

export function ProviderB({ role, children }: { role: Role; children: React.ReactNode }) {
    const [qc] = useState(() => new QueryClient());
    return (
        <QueryClientProvider client={qc}>
            <QuerySettingsProvider value={{ endpoint: '/api/model' }}>
                <RoleB.Provider value={role}>{children}</RoleB.Provider>
            </QuerySettingsProvider>
        </QueryClientProvider>
    );
}

export function SiAutorise(props: { fiche: NomFiche; action: Parameters<typeof peut>[2]; etat?: string; children: React.ReactNode }) {
    return peut(useContext(RoleB), props.fiche, props.action, props.etat) ? <>{props.children}</> : null;
}

// Les pièces sont génériques : le modèle vient de la notice, donc l'accès est dynamique (non typé
// ici) ; le typage porte sur la notice (lib/notice.ts) et sur le code spécifique, s'il y en a.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function useModele(fiche: NomFiche): any {
    return (useClientQueries(schema) as Record<string, unknown>)[NOTICE[fiche].modele];
}
const inclure = (fiche: NomFiche) => Object.fromEntries((NOTICE[fiche].liens ?? []).map((l) => [l.nom, true]));

export function ListeDeFiches({ fiche, lienDetail }: { fiche: NomFiche; lienDetail?: string }) {
    const n = NOTICE[fiche];
    const m = useModele(fiche);
    const { data, isLoading } = m.useFindMany({ include: inclure(fiche), orderBy: n.tri ? { [n.tri.champ]: n.tri.sens } : undefined });
    const [message, setMessage] = useState('');
    const action = n.actionsLigne?.[0];
    const cible = useModele(action?.cree ?? fiche).useCreate();
    if (isLoading) return <p>Chargement…</p>;
    return (
        <section>
            <h1 className="mb-4 text-2xl font-semibold">{n.titre}</h1>
            {message && <p className="mb-4 rounded bg-green-50 p-2 text-sm">{message}</p>}
            <Tableau fiche={n} lignes={data ?? []} lienDetail={lienDetail}
                actions={(l) => action && (
                    <SiAutorise fiche={action.cree} action="creer">
                        <Bouton onClick={() => cible.mutate({ data: { [action.lien]: l.id } },
                            { onSuccess: () => setMessage(`${action.libelle} : demande envoyée.`) })}>
                            {action.libelle}
                        </Bouton>
                    </SiAutorise>
                )} />
        </section>
    );
}

export function FicheDetail({ fiche, id }: { fiche: NomFiche; id: string }) {
    const n = NOTICE[fiche];
    const m = useModele(fiche);
    const { data, isLoading } = m.useFindUnique({ where: { id }, include: inclure(fiche) });
    const maj = m.useUpdate();
    if (isLoading) return <p>Chargement…</p>;
    if (!data) return <p className="text-red-700">Introuvable (ou vous n&apos;y avez pas accès).</p>;
    const etat = n.etat ? String(data[n.etat.champ]) : undefined;
    return (
        <section className="space-y-4">
            <h1 className="text-2xl font-semibold">{n.libelle}</h1>
            <Details fiche={n} ligne={data} />
            <div className="flex gap-2">
                {n.etat && Object.entries(n.etat.boutons).map(([cible, libelle]) => (
                    <SiAutorise key={cible} fiche={fiche} action={`etat:${cible}`} etat={etat}>
                        <Bouton disabled={maj.isPending}
                            onClick={() => maj.mutate({ where: { id }, data: { [n.etat!.champ]: cible } })}>{libelle}</Bouton>
                    </SiAutorise>
                ))}
            </div>
            {maj.isError && <p className="text-red-700">Refusé par le serveur : {String(maj.error?.message)}</p>}
        </section>
    );
}

export function MonProfil({ fiche }: { fiche: NomFiche }) {
    const n = NOTICE[fiche];
    const m = useModele(fiche);
    const { data, isLoading } = m.useFindFirst();
    const maj = m.useUpdate();
    if (isLoading) return <p>Chargement…</p>;
    if (!data) return <p className="text-slate-500">Votre rôle n&apos;a pas de profil.</p>;
    return (
        <section>
            <h1 className="mb-4 text-2xl font-semibold">{n.titre}</h1>
            <Formulaire fiche={n} ligne={data} erreur={String(maj.error?.message ?? '')}
                etat={maj.isPending ? 'en-cours' : maj.isSuccess ? 'ok' : maj.isError ? 'erreur' : 'repos'}
                onSave={(valeurs) => maj.mutate({ where: { id: data.id }, data: valeurs })} />
        </section>
    );
}
