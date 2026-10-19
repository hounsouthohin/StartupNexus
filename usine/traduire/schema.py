"""Traducteur n°1 : matrice → schema.zmodel (données + règles d'accès ZenStack).

Il lit les CASES de la matrice (pas les natures) : les exceptions citées par le brief sont donc
traduites sans code spécial. Patrons : étude 03 ; doctrines : USINE.md §4.
"""
from __future__ import annotations

from ..description import Description
from ..matrice import VISITOR, Matrix
from .modele import FicheApp, bas, construire

ZTYPE = {"texte": "String", "texte_long": "String", "nombre": "Int", "montant": "Decimal", "date": "DateTime",
         "date_heure": "DateTime", "oui_non": "Boolean", "email": "String", "telephone": "String", "url": "String"}


def enum_choix(fiche: str, champ: str) -> str:
    """Le type d'un champ « choix » : une énumération par champ (« BookGenre »)."""
    return f"{fiche}{champ[0].upper()}{champ[1:]}"


def ztype(fiche: str, c) -> str:
    return enum_choix(fiche, c.nom) if c.type == "choix" else ZTYPE[c.type]

ENTETE = """// FICHIER PRODUIT PAR L'USINE — ne pas modifier : il est régénéré à chaque fabrication.
// Tout est REFUSÉ tant qu'une règle @@allow ne l'autorise pas.

datasource db {
    provider = 'postgresql'
    url      = env('DATABASE_URL')
}

plugin policy {
    provider = '@zenstackhq/plugin-policy'
}

// L'utilisateur connecté et son rôle, fournis à chaque requête par la session.
type Auth {
    id   String @id
    role String
    @@auth
}
"""


def _role(a: str) -> str:
    return f"auth().role == '{a}'"


def _et(*parts: str) -> str:
    return " && ".join(p for p in parts if p)


def _ou_etats(etats: list[str]) -> str:
    """« l'état ne change pas » écrit état par état : comparer status à before().status provoque
    une erreur SQL dans ZenStack 3.9.7 (étude 03)."""
    return "(" + " || ".join(f"(before().status == {s} && status == {s})" for s in etats) + ")"


def _inchange(nom: str, facultatif: bool, valeurs: list[str] | None = None) -> str:
    """« ce champ ne bouge pas ». Un champ facultatif peut être vide (NULL) : en SQL, NULL == NULL n'est
    pas vrai, la règle refuserait donc toute étape (trouvé par l'app d'essai des types, N1.1).
    Un champ « choix » (énumération) s'écrit valeur par valeur, comme l'état : comparer une énumération à
    son before() provoque la même erreur SQL dans ZenStack 3.9.7 (trouvé à la répétition temps 2)."""
    if valeurs:
        cas = [f"(before().{nom} == {v} && {nom} == {v})" for v in valeurs]
        return "(" + " || ".join(cas + ([f"({nom} == null && before().{nom} == null)"] if facultatif else [])) + ")"
    egal = f"{nom} == before().{nom}"
    return f"({egal} || ({nom} == null && before().{nom} == null))" if facultatif else egal


def _portee(f: FicheApp, see: str) -> str:
    """Restriction de portée : « les siennes » → la fiche porte l'identifiant de l'utilisateur."""
    return f"{f.proprio} == auth().id" if see == "own" and f.proprio else ""


def regles_enfant(f: FicheApp, m: Matrix, fiches: dict[str, FicheApp]) -> list[str]:
    """(N1.3) Une LIGNE (fiche enfant) : vue par qui voit son parent ; ajoutée, modifiée, retirée selon SA case de
    la matrice (le calculateur la tire du parent : qui modifie le parent, dans ses états — doctrine du 10 oct ; un
    seul auteur, la matrice — le traducteur ne recalcule rien), et sur un parent qu'on voit ; jamais déplacée vers
    un autre parent ; supprimée avec lui (onDelete: Cascade, dans `modele`)."""
    e, out = f.e, []
    lp = next(l for l in f.liens if l.parent)
    parent = fiches[lp.cible]
    autres = [l for l in f.liens if not l.parent and not l.proprietaire]
    parent_lu = f"check({lp.nom}, 'read')"
    for c in (c for c in m.cells if c.entity == e.name):
        a = c.actor
        qui = "true" if a == VISITOR else _role(a)
        if c.see != "none":
            out.append(f"@@allow('read', {_et(qui, parent_lu)})")
        if a == VISITOR:
            continue
        pc = next((x for x in m.cells if x.actor == a and x.entity == parent.nom), None)
        base = [qui, parent_lu]
        if pc is not None and pc.see == "own" and parent.proprio:
            base.append(f"{lp.nom}.{parent.proprio} == auth().id")        # SON parent, s'il ne voit que les siens

        def etats(liste: list[str]) -> str:                              # les états du PARENT où c'est permis
            return "(" + " || ".join(f"{lp.nom}.status == {s}" for s in liste) + ")" if parent.e.process and liste else ""
        cloture = [f"check({l.nom}, 'read')" for l in autres]           # on ne désigne que ce qu'on voit (E2)
        if c.create == "yes":                                            # créer : dans les états que dit la matrice
            out.append(f"@@allow('create', {_et(*base, etats(c.create_while), *cloture)})")
        if c.edit:
            out.append(f"@@allow('update', {_et(*base, etats(c.edit_while))})")
        if c.delete:
            out.append(f"@@allow('delete', {_et(*base, etats(c.delete_while))})")
    out.append(f"@@deny('post-update', {lp.fk} != before().{lp.fk})")   # une ligne ne change jamais de parent
    out.append("@@deny('post-update', createdAt != before().createdAt)")
    for l in autres:
        out.append(f"@@deny('post-update', {l.fk} != before().{l.fk} && !check({l.nom}, 'read'))")
    for rel, _source in f.inverses:
        out.append(f"@@deny('delete', {rel}?[true])")
    return list(dict.fromkeys(out))


def regles(f: FicheApp, m: Matrix, fiches: dict[str, FicheApp]) -> list[str]:
    if f.e.nature == "child":
        return regles_enfant(f, m, fiches)
    e, out = f.e, []
    autres = ([(c.nom, not c.obligatoire, [v.code for v in c.valeurs] if c.type == "choix" else None) for c in f.champs]
              + [(l.fk, False, None) for l in f.liens if not l.proprietaire])
    for c in (c for c in m.cells if c.entity == e.name):
        a = c.actor
        qui = "true" if a == VISITOR else _role(a)          # rôles LISTÉS, jamais « tout connecté » (E4)
        # ── voir ──
        if c.see == "all":
            out.append(f"@@allow('read', {qui})")
        elif c.see == "own" and f.proprio:
            out.append(f"@@allow('read', {_et(qui, _portee(f, 'own'))})")
        elif c.see == "published":
            out.append(f"@@allow('read', {_et(qui, 'published == true')})")
        for v in c.see_via:                                  # « au travers de » : affiché dans une autre fiche
            for rel, source in f.inverses:
                if source == v:
                    out.append(f"@@allow('read', {_et(qui, f'{rel}?[true]')})")
        if a == VISITOR:
            continue                                         # le visiteur ne fait que lire
        # ── créer ──
        if c.create in ("yes", "auto"):
            cond = [qui]
            if e.nature == "profile":
                cond.append("userId == auth().id")
            elif f.proprio and a == e.owner:
                cond.append("ownerId == auth().id")          # pour lui-même, jamais au nom d'un autre
            if e.process:
                cond.append(f"status == {e.process.initial}")  # seulement dans l'état initial
            for l in f.liens:
                if not l.proprietaire:
                    cond.append(f"check({l.nom}, 'read')")   # clôture : on ne pointe que ce qu'on voit (E2)
                    cible = fiches[l.cible]
                    if f.proprio and cible.proprio and cible.e.owner == e.owner and cible.e.nature == "collection":
                        cond.append(f"{l.nom}.ownerId == ownerId")   # cohérence des propriétaires (E2)
            out.append(f"@@allow('create', {_et(*cond)})")
        # ── modifier / faire évoluer l'état ──
        if c.edit or c.transitions:
            out.append(f"@@allow('update', {_et(qui, _portee(f, c.see))})")
        if e.process and c.edit:
            etats = c.edit_while or f.etats
            out.append(f"@@allow('post-update', {_et(qui, _ou_etats(etats))})")
        for depart, cibles in c.transitions.items():         # une règle par flèche ; rien d'autre ne bouge
            arrivee = "(" + " || ".join(f"status == {t}" for t in cibles) + ")"
            inchanges = [_inchange(n, facultatif, valeurs) for n, facultatif, valeurs in autres]
            out.append(f"@@allow('post-update', {_et(qui, f'before().status == {depart}', arrivee, *inchanges)})")
        # ── supprimer (jamais par défaut : seulement si la matrice l'accorde) ──
        if c.delete:
            cond = [qui, _portee(f, c.see)]
            if e.process and c.delete_while:
                cond.append("(" + " || ".join(f"status == {s}" for s in c.delete_while) + ")")
            out.append(f"@@allow('delete', {_et(*cond)})")
    if f.proprio:                                            # le propriétaire ne change jamais
        out.append(f"@@deny('post-update', {f.proprio} != before().{f.proprio})")
    # intégrité : on ne supprime pas une fiche que d'autres désignent — une RÈGLE explicite (doctrine E4 :
    # chaque interdiction est une règle) ; la contrainte de la base (onDelete: Restrict) reste le filet
    for rel, _source in f.inverses:
        out.append(f"@@deny('delete', {rel}?[true])")
    # la date de création non plus (antidater une demande ; trouvé par le testeur v1.2, N1.1)
    out.append("@@deny('post-update', createdAt != before().createdAt)")
    # (N1.2) clôture et cohérence des propriétaires AUSSI À LA MODIFICATION : changer un lien, c'est
    # désigner une autre fiche — seulement une qu'on voit, et du même propriétaire (les formulaires de
    # modification rendent les liens modifiables ; l'écran ne protège rien, le serveur si)
    for l in f.liens:
        if l.proprietaire:
            continue
        out.append(f"@@deny('post-update', {l.fk} != before().{l.fk} && !check({l.nom}, 'read'))")
        cible = fiches[l.cible]
        if f.proprio and cible.proprio and cible.e.owner == e.owner and cible.e.nature == "collection":
            out.append(f"@@deny('post-update', {l.fk} != before().{l.fk} && {l.nom}.ownerId != ownerId)")
        # qui ne voit la fiche visée QU'AU TRAVERS d'autres fiches ne peut pas re-désigner ce lien : la fiche
        # deviendrait visible… grâce au lien qu'il est en train de poser (la vérification tournerait en rond
        # — trou trouvé par le testeur v1.4 sur l'app d'essai)
        for c in m.cells:
            if c.entity == e.name and c.actor != VISITOR and c.edit:
                vue = next((x for x in m.cells if x.actor == c.actor and x.entity == l.cible), None)
                if vue is not None and vue.see == "none":
                    out.append(f"@@deny('post-update', {_role(c.actor)} && {l.fk} != before().{l.fk})")
    return list(dict.fromkeys(out))


def modele(f: FicheApp, m: Matrix, fiches: dict[str, FicheApp]) -> str:
    e = f.e
    # une citation peut tenir sur plusieurs lignes du brief (liste à puces) : en commentaire, UNE ligne
    # (trouvé par la répétition générale : la suite sortait du commentaire et cassait le schéma)
    citation = " ".join(e.citation.split())
    lignes = [f"// {e.nature} · {e.label}" + (f" · {citation}" if citation else ""),
              f"model {e.name} {{", "    id String @id @default(cuid())"]
    if e.nature == "profile":
        lignes.append("    userId String @unique @default(auth().id)")
    elif e.nature == "collection":
        auto = e.process is None or e.process.initiator == e.owner
        lignes.append("    ownerId String" + (" @default(auth().id)" if auto and not e.entered_by else ""))
    for l in f.liens:
        if not l.proprietaire:
            lignes.append(f"    {l.fk} String")
        # onDelete: Restrict — on ne supprime pas une fiche que d'autres fiches désignent (intégrité : jamais
        # de suppression en cascade qui effacerait l'historique sans prévenir). SEULE exception (doctrine du
        # 10 oct) : les lignes d'une fiche partent avec elle (une ligne de devis n'existe pas sans son devis)
        suppression = "Cascade" if l.parent else "Restrict"
        lignes.append(f"    {l.nom} {l.cible} @relation(fields: [{l.fk}], references: [{l.ref}], onDelete: {suppression})")
    for c in f.champs:
        lignes.append(f"    {c.nom} {ztype(e.name, c)}{'' if c.obligatoire else '?'}")
    if e.process:
        lignes.append(f"    status {e.name}Status @default({e.process.initial})")
    lignes.append("    createdAt DateTime @default(now())")
    for rel, source in f.inverses + f.enfants:
        lignes.append(f"    {rel} {source}[]")
    lignes.append("")
    lignes += [f"    {r}" for r in regles(f, m, fiches)]
    lignes.append("}")
    return "\n".join(lignes)


def traduire_schema(desc: Description, m: Matrix) -> str:
    fiches = construire(desc, m)
    blocs = [ENTETE]
    for f in fiches.values():
        if f.etats:
            blocs.append(f"enum {f.nom}Status {{\n" + "\n".join(f"    {s}" for s in f.etats) + "\n}")
        for c in f.champs:
            if c.type == "choix":
                blocs.append(f"enum {enum_choix(f.nom, c.nom)} {{\n" + "\n".join(f"    {v.code}" for v in c.valeurs) + "\n}")
    blocs += [modele(f, m, fiches) for f in fiches.values()]
    return "\n\n".join(blocs) + "\n"
