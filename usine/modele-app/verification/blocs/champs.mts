// BLOC « types de champs » — la partie JUGER de chaque type : comment obtenir une AUTRE valeur
// valide d'un champ (pour essayer « une étape qui change aussi ce champ »). Une ligne par type de la
// base ; un type de champ de l'usine sans sa ligne ici est refusé par le contrôle d'architecture
// (usine/blocs). Les listes de choix (énumérations) sont lues dans le schéma.
import { freshText, kase, modelDef, raw, schema } from '../noyau.mts';

export const AUTRE_VALEUR: Record<string, (v: any) => unknown> = {
    String: () => freshText('autre valeur'),                                                // texte, texte_long, email, telephone, url
    Int: (v) => (v ?? 0) + 1,                                                               // nombre
    Boolean: (v) => !v,                                                                     // oui_non
    DateTime: (v) => new Date((v ? new Date(v).getTime() : Date.UTC(2026, 0, 1)) + 86_400_000), // date, date_heure
    Decimal: (v) => String(Number(v ?? 0) + 1),                                             // montant
};

// Une valeur DIFFÉRENTE de `v`, du type du champ (undefined : type inconnu, signalé).
export function autreValeur(f: any, v: any): unknown {
    if (AUTRE_VALEUR[f.type]) return AUTRE_VALEUR[f.type](v);
    const valeurs: string[] = Object.values(schema.enums?.[f.type]?.values ?? {});           // choix
    if (valeurs.length) return valeurs.find((x) => x !== v);
    console.log(`  ! type de champ inconnu du testeur : ${f.name} (${f.type}) — non essayé`);
    return undefined;
}

// Les autres champs d'une fiche (ni identifiant, ni état), avec une AUTRE valeur valide :
// une étape du circuit ne doit en changer aucun (E4 — trou de couverture corrigé : seul le champ
// « modifiable » était essayé, et seulement sur la première flèche).
export async function otherFieldValues(entity: string, row: any): Promise<[string, unknown][]> {
    const spec = kase.entities[entity];
    const out: [string, unknown][] = [];
    for (const f of Object.values<any>(modelDef(entity).fields)) {
        if (f.id || f.relation || f.name === spec.stateField) continue;
        if (f.foreignKeyFor || f.name === spec.ownerField) {
            const rel = Object.values<any>(modelDef(entity).fields).find((g) => g.relation?.fields?.[0] === f.name);
            const targetModel = rel && kase.entities[rel.type]?.model;
            if (!targetModel) continue;
            const ref = rel.relation.references[0];
            const other = (await raw[targetModel].findMany()).find((r: any) => r[ref] !== row[f.name]);
            if (other) out.push([f.name, other[ref]]);
        } else {
            const autre = autreValeur(f, row[f.name]);       // v1.2 (changement 4) : tous les types
            if (autre !== undefined) out.push([f.name, autre]);
            if (f.optional && row[f.name] != null) out.push([f.name, null]);   // v1.2 (changement 5) : le vider
        }
    }
    return out;
}

// v1.2 (changement 5) : remplit les champs facultatifs vides de la fiche (l'autre moitié des essais).
export const facultatifs = (entity: string) =>
    Object.values<any>(modelDef(entity).fields).filter((f) => f.optional && !f.relation && !f.foreignKeyFor);
export async function remplirFacultatifs(entity: string, id: string): Promise<boolean> {
    const data = Object.fromEntries(facultatifs(entity).map((f) => [f.name, autreValeur(f, null)]).filter(([, v]) => v !== undefined));
    if (!Object.keys(data).length) return false;
    await raw[kase.entities[entity].model].update({ where: { id }, data });
    return true;
}
