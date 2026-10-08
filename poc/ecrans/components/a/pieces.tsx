'use client';
// VARIANTE A — les mêmes pièces génériques, branchées sur Refine. Seule la PLOMBERIE est ici
// (adaptateur Refine → API ZenStack, contrôle d'accès, fonctions de Refine) ; l'affichage est partagé.
import { CanAccess, Refine, useCreate, useList, useOne, useUpdate, type AccessControlProvider,
    type CrudFilter, type DataProvider, type HttpError } from '@refinedev/core';
import routerProvider from '@refinedev/nextjs-router/app';
import { useState } from 'react';
import { Bouton, Details, Formulaire, Tableau } from '@/components/vue/vues';
import { peut, type Action } from '@/lib/matrice';
import { NOTICE, type NomFiche, type Role } from '@/lib/notice';

// ─── Adaptateur Refine → API ZenStack (Refine n'en fournit pas pour ZenStack v3) ─────────────
const API = '/api/model';
const modele = (resource: string) => NOTICE[resource as NomFiche].modele;
async function appel(model: string, op: string, method: string, args: unknown) {
    const dansUrl = method === 'GET' || method === 'DELETE';
    const res = await fetch(`${API}/${model}/${op}${dansUrl ? `?q=${encodeURIComponent(JSON.stringify(args))}` : ''}`, {
        method, headers: { 'content-type': 'application/json' }, body: dansUrl ? undefined : JSON.stringify(args),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw { message: body?.error?.message ?? res.statusText, statusCode: res.status } as HttpError;
    return body.data;
}
const ou = (filters?: CrudFilter[]) =>
    Object.fromEntries((filters ?? []).flatMap((f) => ('field' in f && f.operator === 'eq' ? [[f.field, f.value]] : [])));
const dataProvider: DataProvider = {
    getApiUrl: () => API,
    getList: async ({ resource, filters, sorters, meta }) => {
        const where = ou(filters);
        const [data, total] = await Promise.all([
            appel(modele(resource), 'findMany', 'GET', { where, include: meta?.include, orderBy: sorters?.map((s) => ({ [s.field]: s.order })) }),
            appel(modele(resource), 'count', 'GET', { where }),
        ]);
        return { data, total };
    },
    getOne: async ({ resource, id, meta }) => {
        const data = await appel(modele(resource), 'findUnique', 'GET', { where: { id }, include: meta?.include });
        if (!data) throw { message: 'Introuvable', statusCode: 404 } as HttpError;
        return { data };
    },
    create: async ({ resource, variables }) => ({ data: await appel(modele(resource), 'create', 'POST', { data: variables }) }),
    update: async ({ resource, id, variables }) => ({ data: await appel(modele(resource), 'update', 'PUT', { where: { id }, data: variables }) }),
    deleteOne: async ({ resource, id }) => ({ data: await appel(modele(resource), 'delete', 'DELETE', { where: { id } }) }),
};

export function ProviderA({ role, children }: { role: Role; children: React.ReactNode }) {
    const accessControlProvider: AccessControlProvider = {
        can: async ({ resource, action, params }) => ({ can: peut(role, resource as NomFiche, action as Action, params?.etat) }),
    };
    return (
        <Refine dataProvider={dataProvider} routerProvider={routerProvider} accessControlProvider={accessControlProvider}
            resources={(Object.keys(NOTICE) as NomFiche[]).map((name) => ({ name }))}
            options={{ disableTelemetry: true, syncWithLocation: false }}>
            {children}
        </Refine>
    );
}

const inclure = (fiche: NomFiche) => Object.fromEntries((NOTICE[fiche].liens ?? []).map((l) => [l.nom, true]));

export function ListeDeFiches({ fiche, lienDetail }: { fiche: NomFiche; lienDetail?: string }) {
    const n = NOTICE[fiche];
    const { result, query } = useList({
        resource: fiche, pagination: { mode: 'off' }, meta: { include: inclure(fiche) },
        sorters: n.tri ? [{ field: n.tri.champ, order: n.tri.sens }] : [],
    });
    const { mutate: creer } = useCreate();
    const [message, setMessage] = useState('');
    const action = n.actionsLigne?.[0];
    if (query.isLoading) return <p>Chargement…</p>;
    return (
        <section>
            <h1 className="mb-4 text-2xl font-semibold">{n.titre}</h1>
            {message && <p className="mb-4 rounded bg-green-50 p-2 text-sm">{message}</p>}
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <Tableau fiche={n} lignes={result.data as any[]} lienDetail={lienDetail}
                actions={(l) => action && (
                    <CanAccess resource={action.cree} action="creer">
                        <Bouton onClick={() => creer({ resource: action.cree, values: { [action.lien]: l.id }, successNotification: false },
                            { onSuccess: () => setMessage(`${action.libelle} : demande envoyée.`) })}>
                            {action.libelle}
                        </Bouton>
                    </CanAccess>
                )} />
        </section>
    );
}

export function FicheDetail({ fiche, id }: { fiche: NomFiche; id: string }) {
    const n = NOTICE[fiche];
    const { result: data, query } = useOne({ resource: fiche, id, meta: { include: inclure(fiche) } });
    const { mutate: maj, mutation } = useUpdate();
    if (query.isLoading) return <p>Chargement…</p>;
    if (query.isError || !data) return <p className="text-red-700">Introuvable (ou vous n&apos;y avez pas accès).</p>;
    const etat = n.etat ? String(data[n.etat.champ]) : undefined;
    return (
        <section className="space-y-4">
            <h1 className="text-2xl font-semibold">{n.libelle}</h1>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <Details fiche={n} ligne={data as any} />
            <div className="flex gap-2">
                {n.etat && Object.entries(n.etat.boutons).map(([cible, libelle]) => (
                    <CanAccess key={cible} resource={fiche} action={`etat:${cible}`} params={{ etat }}>
                        <Bouton disabled={mutation.isPending}
                            onClick={() => maj({ resource: fiche, id, values: { [n.etat!.champ]: cible }, successNotification: false })}>
                            {libelle}
                        </Bouton>
                    </CanAccess>
                ))}
            </div>
            {mutation.isError && <p className="text-red-700">Refusé par le serveur : {mutation.error?.message}</p>}
        </section>
    );
}

export function MonProfil({ fiche }: { fiche: NomFiche }) {
    const n = NOTICE[fiche];
    const { result, query } = useList({ resource: fiche, pagination: { mode: 'off' } });
    const { mutate: maj, mutation } = useUpdate();
    const ligne = result.data[0];
    if (query.isLoading) return <p>Chargement…</p>;
    if (!ligne) return <p className="text-slate-500">Votre rôle n&apos;a pas de profil.</p>;
    return (
        <section>
            <h1 className="mb-4 text-2xl font-semibold">{n.titre}</h1>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <Formulaire fiche={n} ligne={ligne as any} erreur={mutation.error?.message}
                etat={mutation.isPending ? 'en-cours' : mutation.isSuccess ? 'ok' : mutation.isError ? 'erreur' : 'repos'}
                onSave={(valeurs) => maj({ resource: fiche, id: String(ligne.id), values: valeurs, successNotification: false })} />
        </section>
    );
}
