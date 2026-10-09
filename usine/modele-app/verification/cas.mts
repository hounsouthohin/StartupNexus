// L'adaptateur du testeur, CONSTRUIT depuis la description de l'app (au lieu d'être écrit à la main
// comme dans poc/regles) : quelles fiches, à qui, quels liens, et des données de test valides.
// Règles de l'E4 : au moins 2 fiches de chaque sorte, 2 propriétaires par rôle, un 3e utilisateur
// sans profil (pour l'essai « première connexion »).
// Règle N1.0 (trou trouvé par mutation) : chaque sorte a aussi au moins une fiche RELIÉE À RIEN, sinon
// « ne voir que les fiches reliées » ne se distingue pas de « tout voir ». Catalogue, registre : les liens
// visent toujours la 1re fiche, la 2e reste libre. Profil : un 4e utilisateur qui n'a que son profil.
// Règle N1.1 (défaut réel trouvé : NULL == NULL n'est pas vrai en SQL) : les champs FACULTATIFS restent
// vides dans les données ; le testeur (v1.2) les remplit lui-même pour l'autre moitié des essais.
import type { Case, EntitySpec, User, Users, World } from './noyau.mts';

type Champ = { nom: string; type: string; libelle: string; obligatoire?: boolean; valeurs?: { code: string }[] };
type Entite = { name: string; nature: string; owner?: string | null; references?: string[]; process?: unknown };

const bas = (n: string) => n[0].toLowerCase() + n.slice(1);

function valeur(c: Champ, i: number): unknown {
    switch (c.type) {
        case 'email': return `essai${i}@exemple.invalid`;
        case 'telephone': return `060000000${i}`;
        case 'url': return `https://exemple.invalid/${i}`;
        case 'nombre': return i;
        case 'montant': return `${i}.50`;
        case 'choix': return c.valeurs![i % c.valeurs!.length].code;
        case 'date': case 'date_heure': return new Date(2026, 0, 1 + i);
        case 'oui_non': return i % 2 === 0;
        default: return `${c.libelle} ${i}`;
    }
}

export function construireCas(description: any, depart: any): Case {
    const entites: Entite[] = description.acces.entities;
    const parNom = Object.fromEntries(entites.map((e) => [e.name, e]));
    const champs: Record<string, Champ[]> = description.champs ?? {};
    // le même découpage des liens que l'usine (usine/traduire/modele.py)
    const liens = (e: Entite) => (e.references ?? []).map((r) => {
        const cible = parNom[r];
        const proprietaire = cible.nature === 'profile' && e.nature === 'collection' && cible.owner === e.owner;
        return { cible: r, fk: proprietaire ? null : `${bas(r)}Id` };
    });
    let n = 0;
    const entities: Record<string, EntitySpec> = {};
    for (const e of entites) {
        const texte = (champs[e.name] ?? []).find((c) => c.type === 'texte' || c.type === 'texte_long');
        entities[e.name] = {
            model: bas(e.name),
            ownerField: e.nature === 'profile' ? 'userId' : e.nature === 'collection' ? 'ownerId' : undefined,
            profile: e.nature === 'profile',
            stateField: e.process ? 'status' : undefined,
            editField: texte?.nom,
            build: (w: World, owner: User | null) => {
                n++;
                const data: Record<string, unknown> = Object.fromEntries((champs[e.name] ?? [])
                    .filter((c) => c.obligatoire !== false).map((c) => [c.nom, valeur(c, n)]));
                if (e.nature === 'profile') data.userId = owner!.id;
                if (e.nature === 'collection') data.ownerId = owner!.id;
                for (const l of liens(e)) if (l.fk) data[l.fk] = w[`${l.cible}:${owner?.id}`] ?? w[l.cible];
                return data;
            },
        };
    }
    const creation: string[] = depart.creation;
    const nomDe = Object.fromEntries(entites.map((e) => [bas(e.name), e.name]));
    return {
        matrix: description.app.nom,
        roles: description.acces.actors.map((a: { id: string }) => a.id),
        entities,
        resetOrder: depart.suppression,
        seed: async (raw: any, users: Users) => {
            const w: World = {};
            for (const modele of creation) {
                const e = parNom[nomDe[modele]];
                const spec = entities[e.name];
                const proprietaires = e.nature === 'profile' || e.nature === 'collection' ? users[e.owner!].slice(0, 2) : [null, null];
                for (const u of proprietaires) {
                    const fiche = await raw[spec.model].create({ data: spec.build(w, u) });
                    w[e.name] ??= fiche.id;
                    if (u) w[`${e.name}:${u.id}`] = fiche.id;
                }
                // la fiche reliée à rien : jamais rangée dans w, donc aucune autre fiche ne la désigne
                if (e.nature === 'profile') await raw[spec.model].create({ data: spec.build(w, { id: `${e.owner}_4`, role: e.owner! }) });
            }
            return w;
        },
    };
}
