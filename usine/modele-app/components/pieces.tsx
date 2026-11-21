'use client';
// Les PIÈCES génériques, branchées sur les fonctions que ZenStack génère depuis le schéma
// (@zenstackhq/tanstack-query) — étude 06. Elles ne connaissent aucun métier : elles lisent la
// notice et les droits produits par l'usine.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { QuerySettingsProvider, useClientQueries } from '@zenstackhq/tanstack-query/react';
import { useRouter } from 'next/navigation';
import { createContext, useContext, useState } from 'react';
import { Bouton, Details, Formulaire, Tableau, lireChemin, titreDe } from '@/components/vues';
import type { Role } from '@/lib/droits';
import type { Lien } from '@/lib/fiche';
import { NOTICE, type NomFiche } from '@/lib/notice';
import { peut, type Action } from '@/lib/peut';
import { schema } from '@/zenstack/schema';

const RoleActuel = createContext<Role>('visitor');
export const useRole = () => useContext(RoleActuel);
const PersonneActuelle = createContext<string>('');
export const usePersonne = () => useContext(PersonneActuelle);

export function Fournisseur({ role, personne, children }: { role: Role; personne: string; children: React.ReactNode }) {
    const [qc] = useState(() => new QueryClient());
    return (
        <QueryClientProvider client={qc}>
            <QuerySettingsProvider value={{ endpoint: '/api/model' }}>
                <RoleActuel.Provider value={role}>
                    <PersonneActuelle.Provider value={personne}>{children}</PersonneActuelle.Provider>
                </RoleActuel.Provider>
            </QuerySettingsProvider>
        </QueryClientProvider>
    );
}

export function SiAutorise(props: { fiche: NomFiche; action: Action; etat?: string; children: React.ReactNode }) {
    return peut(useRole(), props.fiche, props.action, props.etat) ? <>{props.children}</> : null;
}

// Pièces génériques : le modèle vient de la notice, l'accès est donc dynamique ; la sécurité de
// type vient de la notice typée (étude 06).
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function useModele(fiche: NomFiche): any {
    return (useClientQueries(schema) as Record<string, unknown>)[NOTICE[fiche].modele];
}
// les fiches liées, et (contrat des noms à l'écran) la fiche que la fiche liée désigne quand son titre en vient
// (« book.title » : un seul niveau)
const inclureAffiche = (affiche: string) => (affiche.includes('.') ? { include: { [affiche.split('.')[0]]: true } } : true);
const inclure = (fiche: NomFiche) => Object.fromEntries((NOTICE[fiche].liens ?? []).map((l) => [l.nom, inclureAffiche(l.affiche)]));
const majuscule = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

// (contrat des noms à l'écran, règle 11) L'ÉTAT D'UNE ZONE DE DONNÉES, pour la machine : chargement, prêt, erreur.
// Une erreur s'affiche comme une erreur, JAMAIS comme une liste vide ; une liste vide et prête dit « Aucun élément ».
// Exportées pour l'artisan (CONTRAT-ECRANS.md) : ses écrans de `sur-mesure/` portent leur état de la même façon.
export type EtatZone = 'chargement' | 'pret' | 'erreur';
export const etatZone = (q: { isLoading: boolean; isError: boolean }): EtatZone => (q.isLoading ? 'chargement' : q.isError ? 'erreur' : 'pret');
export function Zone(props:{ zone: 'liste' | 'fiche' | 'choix'; fiche: string; etat: EtatZone; erreur?: unknown; className?: string; children?: React.ReactNode }) {
    return (
        <section data-zone={props.zone} data-fiche={props.fiche} data-etat={props.etat} aria-busy={props.etat === 'chargement'}
            className={props.className}>
            {props.etat === 'chargement' ? <p data-chargement="">Chargement…</p>
                : props.etat === 'erreur' ? <p className="text-red-700" role="alert">Erreur de chargement : {String((props.erreur as Error)?.message ?? props.erreur ?? '')}</p>
                : props.children}
        </section>
    );
}

type ActionLigne = { libelle: string; cree: string; lien: string };

export function ListeDeFiches({ fiche, lienDetail }: { fiche: NomFiche; lienDetail?: string }) {
    const n = NOTICE[fiche];
    const m = useModele(fiche);
    const q = m.useFindMany({ include: inclure(fiche), orderBy: n.tri ? { [n.tri.champ]: n.tri.sens } : undefined });
    const { data } = q;
    const [message, setMessage] = useState('');
    const [refus, setRefus] = useState('');
    const [creation, setCreation] = useState(false);
    // (contrat, zone « liste ») elle enveloppe le titre, le bouton de création, le formulaire et les lignes ; elle
    // existe pendant le chargement
    return (
        <Zone zone="liste" fiche={fiche} etat={etatZone(q)} erreur={q.error}>
            <div className="mb-4 flex items-center justify-between gap-4">
                <h1 className="text-2xl font-semibold">{n.titre}</h1>
                {n.creation && (
                    <SiAutorise fiche={fiche} action="creer">
                        <Bouton onClick={() => { setCreation(!creation); setMessage(''); }}>{n.creation.libelle}</Bouton>
                    </SiAutorise>
                )}
            </div>
            {creation && (
                <div className="mb-4">
                    <CreationFiche key={fiche} fiche={fiche}
                        onCree={() => { setCreation(false); setRefus(''); setMessage('Enregistré.'); }} />
                </div>
            )}
            {message && <p className="mb-4 rounded bg-green-50 p-2 text-sm">{message}</p>}
            {refus && <p className="mb-4 rounded bg-red-50 p-2 text-sm">Refusé : {refus}</p>}
            {/* TOUS les boutons de création d'une ligne (une fiche peut en avoir plusieurs : trouvé par la
                répétition générale — seul le premier s'affichait) */}
            <Tableau fiche={n} lignes={data ?? []} lienDetail={lienDetail}
                actions={(l) => (n.actionsLigne ?? []).map((a) => (
                    <SiAutorise key={`${a.cree}:${a.lien}`} fiche={a.cree as NomFiche} action="creer">
                        <BoutonCreer action={a} ligneId={l.id} onFait={(t) => { setRefus(''); setMessage(t); }} onRefus={setRefus} />
                    </SiAutorise>
                ))} />
        </Zone>
    );
}

// Un bouton de création d'un clic : sa propre pièce, avec sa propre fonction de création.
function BoutonCreer({ action, ligneId, onFait, onRefus }: {
    action: ActionLigne; ligneId: string; onFait: (t: string) => void; onRefus: (t: string) => void;
}) {
    const cible = useModele(action.cree as NomFiche).useCreate();
    return (
        <Bouton disabled={cible.isPending}
            onClick={() => cible.mutate({ data: { [action.lien]: ligneId } }, {
                onSuccess: () => onFait(`${action.libelle} : demande enregistrée.`),
                onError: (e: Error) => onRefus(String(e?.message)),
            })}>
            {action.libelle}
        </Bouton>
    );
}

// (N1.2) La liste de choix d'une fiche liée : seulement les fiches que la personne a le droit de voir
// (le serveur refuse de toute façon les autres — clôture, à la création comme à la modification).
function ChoixLien({ lien, valeur, id }: { lien: Lien; valeur: string; id: string }) {
    // (contrat) une fiche liée se montre par son titre ; s'il vient d'une fiche qu'elle désigne, on l'inclut
    const champ = lien.affiche.includes('.') ? lien.affiche.split('.')[0] : null;
    const q = useModele(lien.cible as NomFiche).useFindMany(champ ? { include: { [champ]: true } } : undefined);
    const lignes: Record<string, unknown>[] = q.data ?? [];
    const etat = etatZone(q);
    // en modification, la valeur actuelle reste proposée même si la personne ne voit pas la fiche liée :
    // sinon l'enregistrement changerait le lien sans qu'elle l'ait voulu
    const cachee = !!valeur && !lignes.some((l) => String(l.id) === valeur);
    return (
        // (contrat, zone « choix ») data-fiche = la fiche CIBLE ; data-chargement : le formulaire ne part pas tant qu'une
        // liste de choix charge (sinon le lien partait vide)
        <Zone zone="choix" fiche={lien.cible} etat={etat} erreur={q.error}>
            {etat === 'pret' && !lignes.length && !valeur ? (
                <p className="text-red-700">Aucun(e) {lien.libelle.toLowerCase()} à choisir.</p>
            ) : (
                <select id={id} name={lien.fk} required defaultValue={valeur || String(lignes[0]?.id ?? '')} className="mt-1 block w-full rounded border p-2">
                    {cachee && <option value={valeur}>— inchangé —</option>}
                    {lignes.map((l) => <option key={String(l.id)} value={String(l.id)}>{String(lireChemin(l, lien.affiche) ?? l.id)}</option>)}
                </select>
            )}
        </Zone>
    );
}
const choixLien = (lien: Lien, valeur: string, id: string) => <ChoixLien lien={lien} valeur={valeur} id={id} />;

// (N1.2) Le formulaire de création d'une fiche (ses champs, et ses fiches liées à choisir).
function CreationFiche({ fiche, onCree }: { fiche: NomFiche; onCree: () => void }) {
    const n = NOTICE[fiche];
    const cree = useModele(fiche).useCreate();
    return (
        <Formulaire fiche={n} bouton="Créer" choixLien={choixLien} erreur={String(cree.error?.message ?? '')}
            etat={cree.isPending ? 'en-cours' : cree.isError ? 'erreur' : 'repos'}
            onSave={(valeurs) => cree.mutate({ data: valeurs }, { onSuccess: onCree })} />
    );
}

export function FicheDetail({ fiche, id }: { fiche: NomFiche; id: string }) {
    const n = NOTICE[fiche];
    const m = useModele(fiche);
    const q = m.useFindUnique({
        where: { id },
        include: { ...inclure(fiche), ...Object.fromEntries((n.designee_par ?? []).map((d) => [d.relation, { select: { id: true } }])) },
    });
    const { data } = q;
    const maj = m.useUpdate();
    const supp = m.useDelete();
    const router = useRouter();
    const [modification, setModification] = useState(false);
    const [confirmer, setConfirmer] = useState(false);
    // (contrat, zone « fiche ») elle enveloppe toute la page de la fiche ; une fiche absente ou interdite est un état
    // PRÊT (la réponse est arrivée : rien à montrer), une panne est une ERREUR
    if (!data) return (
        <Zone zone="fiche" fiche={fiche} etat={etatZone(q)} erreur={q.error}>
            <p className="text-red-700">Introuvable (ou vous n&apos;y avez pas accès).</p>
        </Zone>
    );
    const etat = n.etat ? String(data[n.etat.champ]) : undefined;
    // intégrité : une fiche que d'autres désignent ne se supprime pas — l'écran dit pourquoi
    const utilisee = (n.designee_par ?? [])
        .map((d) => ({ d, nombre: (data[d.relation] as unknown[] | undefined)?.length ?? 0 }))
        .filter((x) => x.nombre > 0)
        .map((x) => `${x.nombre} ${x.nombre > 1 ? x.d.libelle : x.d.libelle_un}`);
    return (
        <Zone zone="fiche" fiche={fiche} etat="pret" className="space-y-4">
            {/* (contrat, règle 3) le repère d'une fiche : sa sorte ET son titre (« Ouvrage : Le Petit Prince ») */}
            <h1 className="text-2xl font-semibold">{n.titreFiche ? `${majuscule(n.libelle)} : ${titreDe(n, data)}` : n.libelle}</h1>
            <Details fiche={n} ligne={data} />
            {/* les décisions du circuit (data-bloc : les tests d'écran les distinguent des autres boutons) */}
            <div className="flex gap-2" data-bloc="decision">
                {n.etat && Object.entries(n.etat.boutons).map(([cible, libelle]) => (
                    <SiAutorise key={cible} fiche={fiche} action={`etat:${cible}`} etat={etat}>
                        <Bouton disabled={maj.isPending}
                            onClick={() => maj.mutate({ where: { id }, data: { [n.etat!.champ]: cible } })}>{libelle}</Bouton>
                    </SiAutorise>
                ))}
            </div>
            {/* (N1.2) modifier et supprimer, seulement si la matrice le permet (dans l'état actuel) */}
            <div className="flex gap-2" data-bloc="gestion">
                <SiAutorise fiche={fiche} action="modifier" etat={etat}>
                    <Bouton onClick={() => setModification(!modification)}>Modifier</Bouton>
                </SiAutorise>
                <SiAutorise fiche={fiche} action="supprimer" etat={etat}>
                    {utilisee.length ? (
                        <span className="flex items-center gap-2">
                            <Bouton disabled onClick={() => undefined}>Supprimer</Bouton>
                            <span className="text-sm text-slate-500">
                                Cette fiche est utilisée par {utilisee.join(', ')} : impossible de la supprimer.
                            </span>
                        </span>
                    ) : confirmer ? (
                        <Bouton disabled={supp.isPending}
                            onClick={() => supp.mutate({ where: { id } }, { onSuccess: () => router.push(`/f/${fiche}`) })}>
                            Confirmer la suppression
                        </Bouton>
                    ) : (
                        <Bouton onClick={() => setConfirmer(true)}>Supprimer</Bouton>
                    )}
                </SiAutorise>
            </div>
            {modification && (
                <Formulaire fiche={n} ligne={data} choixLien={choixLien} erreur={String(maj.error?.message ?? '')}
                    etat={maj.isPending ? 'en-cours' : maj.isSuccess ? 'ok' : maj.isError ? 'erreur' : 'repos'}
                    onSave={(valeurs) => maj.mutate({ where: { id }, data: valeurs }, { onSuccess: () => setModification(false) })} />
            )}
            {maj.isError && !modification && <p className="text-red-700">Refusé par le serveur : {String(maj.error?.message)}</p>}
            {supp.isError && <p className="text-red-700">Refusé par le serveur : {String(supp.error?.message)}</p>}
            {/* (N1.3) les lignes de cette fiche (fiches enfants) */}
            {(n.enfants ?? []).map((enfant) => (
                <SiAutorise key={enfant.fiche} fiche={enfant.fiche as NomFiche} action="voir">
                    <Lignes parent={fiche} parentId={id} etatParent={etat} enfant={enfant} />
                </SiAutorise>
            ))}
        </Zone>
    );
}

// (N1.3) Les LIGNES d'une fiche (fiches enfants), dans la page de leur parent : vues par qui voit le parent ;
// ajoutées, modifiées, retirées par qui peut modifier le parent DANS SON ÉTAT (doctrine du 10 oct) — le
// serveur le vérifie de toute façon. data-bloc : les tests d'écran trouvent la section.
function Lignes({ parent, parentId, etatParent, enfant }: {
    parent: NomFiche; parentId: string; etatParent?: string;
    enfant: { fiche: string; fk: string; libelle: string; libelle_un: string };
}) {
    const nom = enfant.fiche as NomFiche;
    const n = NOTICE[nom];
    const m = useModele(nom);
    const role = useRole();
    const { data, isLoading } = m.useFindMany({
        where: { [enfant.fk]: parentId }, include: inclure(nom),
        orderBy: n.tri ? { [n.tri.champ]: n.tri.sens } : { createdAt: 'asc' },
    });
    const ajoute = m.useCreate();
    const maj = m.useUpdate();
    const retire = m.useDelete();
    const [ajout, setAjout] = useState(false);
    const [enModification, setEnModification] = useState<string | null>(null);
    const [aRetirer, setARetirer] = useState<string | null>(null);
    // affordance honnête : les gestes suivent la case de la LIGNE dans la matrice (tirée du parent par le
    // calculateur), jugée dans l'état actuel du parent — l'écran ne recalcule rien
    const peutAjouter = peut(role, nom, 'creer', etatParent);
    const peutModifier = peut(role, nom, 'modifier', etatParent);
    const peutRetirer = peut(role, nom, 'supprimer', etatParent);
    if (isLoading) return <p>Chargement…</p>;
    const lignes: (Record<string, unknown> & { id: string })[] = data ?? [];
    const enCours = lignes.find((l) => String(l.id) === enModification);
    const erreur = ajoute.error ?? maj.error ?? retire.error;
    return (
        <section className="space-y-2" data-bloc="lignes" data-fiche={nom}>
            <div className="flex items-center justify-between gap-4">
                <h2 className="text-lg font-semibold">{enfant.libelle}</h2>
                {peutAjouter && <Bouton onClick={() => { setAjout(!ajout); setEnModification(null); }}>Ajouter : {enfant.libelle_un}</Bouton>}
            </div>
            {ajout && (
                <Formulaire fiche={n} bouton="Ajouter" choixLien={choixLien} erreur={String(ajoute.error?.message ?? '')}
                    etat={ajoute.isPending ? 'en-cours' : ajoute.isError ? 'erreur' : 'repos'}
                    onSave={(valeurs) => ajoute.mutate({ data: { ...valeurs, [enfant.fk]: parentId } }, { onSuccess: () => setAjout(false) })} />
            )}
            <Tableau fiche={n} lignes={lignes} actions={(l) => (
                <>
                    {peutModifier && <Bouton onClick={() => { setEnModification(String(l.id)); setAjout(false); }}>Modifier la ligne</Bouton>}
                    {peutRetirer && (aRetirer === String(l.id) ? (
                        <Bouton disabled={retire.isPending} onClick={() => retire.mutate({ where: { id: l.id } }, { onSuccess: () => setARetirer(null) })}>
                            Confirmer le retrait
                        </Bouton>
                    ) : (
                        <Bouton onClick={() => setARetirer(String(l.id))}>Retirer</Bouton>
                    ))}
                </>
            )} />
            {enCours && (
                <Formulaire fiche={n} ligne={enCours} choixLien={choixLien} erreur={String(maj.error?.message ?? '')}
                    etat={maj.isPending ? 'en-cours' : maj.isError ? 'erreur' : 'repos'}
                    onSave={(valeurs) => maj.mutate({ where: { id: enCours.id }, data: valeurs }, { onSuccess: () => setEnModification(null) })} />
            )}
            {erreur && !ajout && !enCours && <p className="text-red-700">Refusé par le serveur : {String((erreur as Error).message)}</p>}
        </section>
    );
}

export function MonProfil({ fiche }: { fiche: NomFiche }) {
    const n = NOTICE[fiche];
    const m = useModele(fiche);
    const personne = usePersonne();
    const modifiable = peut(useRole(), fiche, 'modifier');
    const { data, isLoading } = m.useFindFirst({ where: { userId: personne } });   // le SIEN, pas un autre
    const maj = m.useUpdate();
    if (isLoading) return <p>Chargement…</p>;
    if (!data) return <p className="text-slate-500">Votre rôle n&apos;a pas de profil.</p>;
    // (répétition temps 2) affordance honnête : si le rôle ne peut pas modifier son profil (« seuls les
    // administrateurs modifient »), on le montre en lecture seule — pas de bouton « Enregistrer » refusé
    return (
        <section>
            <h1 className="mb-4 text-2xl font-semibold">Mon {n.libelle}</h1>
            {modifiable ? (
                <Formulaire fiche={n} ligne={data} erreur={String(maj.error?.message ?? '')}
                    etat={maj.isPending ? 'en-cours' : maj.isSuccess ? 'ok' : maj.isError ? 'erreur' : 'repos'}
                    onSave={(valeurs) => maj.mutate({ where: { id: data.id }, data: valeurs })} />
            ) : (
                <Details fiche={n} ligne={data} />
            )}
        </section>
    );
}
