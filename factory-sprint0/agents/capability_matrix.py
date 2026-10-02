"""
agents/capability_matrix.py — la matrice des capacités (USINE.md §4.3, phase 3).

Entrée  : AccessDeclaration — acteurs (et comment on le devient), entités avec leur nature,
          processus (qui lance, qui décide), exceptions citées du brief.
Sortie  : Matrix — une case par (acteur × entité) : voir / créer / modifier / supprimer /
          faire évoluer l'état, avec la raison de chaque droit (règle 7 : traçabilité).
Dérivés : pages, navigation et tableau de bord par acteur ; phrases et questions du miroir.

Fonctions pures, sans IA ni I/O, indépendantes de la stack : les URL et le code sont l'affaire
des générateurs (phase 5).

Préréglages au MOINDRE PRIVILÈGE : un acteur ne reçoit que ce que son rôle rend nécessaire ;
tout le reste exige une exception citant le brief. Une exception oubliée donne un manque
visible, jamais une fuite invisible. Supprimer n'est accordé par défaut à PERSONNE (il faut
« gérer » ou « supprimer » dans le brief).
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VISITOR = "visitor"


# ══════════════════════════════════════════════════════════════════════════
# Entrée : la déclaration d'accès
# ══════════════════════════════════════════════════════════════════════════

class _Strict(BaseModel):
    """Règle 3 (USINE §4.6) : un champ inconnu est refusé, jamais ignoré en silence."""
    model_config = ConfigDict(extra="forbid")


class Actor(_Strict):
    id: str
    label: str
    label_plural: str = ""                  # « secrétaires » (défaut : label + « s »)
    # Comment on devient cet acteur (règle de clôture : un chemin, et un seul).
    becomes: Literal["signup", "bootstrap", "invited"]
    invited_by: str | None = None          # obligatoire si becomes == "invited"
    citation: str = ""


class Process(_Strict):
    """Cycle de vie d'une collection : qui lance, qui fait évoluer l'état."""
    field: str = "status"
    initial: str
    transitions: dict[str, list[str]]
    initiator: str                          # qui crée : le propriétaire, ou quelqu'un pour son compte
    decider: str                            # qui fait évoluer l'état ; peut être le propriétaire
    # Étapes faites par un autre acteur que le décideur : état de départ → acteur
    # (ex. notes de frais : {draft: employee} — l'employé soumet, le responsable fait le reste).
    steps_by: dict[str, str] = Field(default_factory=dict)
    labels: dict[str, str] = Field(default_factory=dict)    # état → libellé (« requested » → « demandé »)
    citation: str = ""


class Entity(_Strict):
    name: str
    label: str                              # « emprunt »
    label_plural: str                       # « emprunts »
    feminine: bool = False                  # « toutes les réparations » / « mes réparations »
    nature: Literal["profile", "catalog", "collection", "child"]
    owner: str | None = None                # profil : l'acteur ; collection : le propriétaire
    # Catalogue : qui le gère (un acteur ou une liste) ; None = lecture seule.
    manager: str | list[str] | None = None
    public: bool = False                    # le visiteur le voit (catalogue, ou enfant explicitement public)
    publication: bool = False               # brouillon / publié : les non-gestionnaires ne voient que le publié
    # Collection saisie par un autre acteur POUR le propriétaire (le patron note le véhicule du
    # client) : il crée et modifie ; le propriétaire suit. Avec un processus : Process.initiator.
    entered_by: str | None = None
    parent: str | None = None               # enfant : l'entité parente
    references: list[str] = Field(default_factory=list)   # entités référencées (clés étrangères)
    process: Process | None = None
    citation: str = ""

    @property
    def managers(self) -> list[str]:
        if self.manager is None:
            return []
        return [self.manager] if isinstance(self.manager, str) else list(self.manager)


Action = Literal["see", "create", "edit", "delete", "transition"]


class AccessException(_Strict):
    """Écart au préréglage, toujours justifié par une phrase du brief."""
    actor: str
    entity: str
    action: Action
    allow: bool = True
    scope: Literal["own", "all"] = "own"    # pour « see »
    while_states: list[str] = Field(default_factory=list)       # edit / delete : seulement dans ces états
    transitions: dict[str, list[str]] = Field(default_factory=dict)  # pour « transition »
    citation: str


class AccessDeclaration(_Strict):
    actors: list[Actor]
    entities: list[Entity]
    exceptions: list[AccessException] = Field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════
# Sortie : la matrice
# ══════════════════════════════════════════════════════════════════════════

class Cell(BaseModel):
    actor: str
    entity: str
    # Parcourir (donne des pages et une entrée de menu) : rien, les siens, les publiés, tout.
    see: Literal["none", "own", "published", "all"] = "none"
    # Visible seulement AU TRAVERS de ces entités (affiché dans leur fiche), sans page propre :
    # ce que la clôture accorde. Parcourir l'entité resterait un désir (miroir).
    see_via: list[str] = Field(default_factory=list)
    create: Literal["no", "yes", "auto"] = "no"
    edit: bool = False
    edit_while: list[str] = Field(default_factory=list)      # vide = dans tous les états
    delete: bool = False
    delete_while: list[str] = Field(default_factory=list)
    transitions: dict[str, list[str]] = Field(default_factory=dict)
    why: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)   # citations du brief qui justifient la case


class Issue(BaseModel):
    level: Literal["error", "warning", "info"]
    message: str


class Matrix(BaseModel):
    actors: list[str]                       # visiteur en premier
    entities: list[str]
    cells: list[Cell]
    auto_links: list[str] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)

    def cell(self, actor: str, entity: str) -> Cell:
        for c in self.cells:
            if c.actor == actor and c.entity == entity:
                return c
        raise KeyError(f"{actor}/{entity}")

    @property
    def errors(self) -> list[str]:
        return [i.message for i in self.issues if i.level == "error"]


# ══════════════════════════════════════════════════════════════════════════
# Calcul
# ══════════════════════════════════════════════════════════════════════════

def _norm(text: str) -> str:
    text = text.lower().replace("’", "'").replace("«", '"').replace("»", '"')
    return re.sub(r"\s+", " ", text).strip()


def compute_matrix(decl: AccessDeclaration, brief: str | None = None) -> Matrix:
    """Calcule la matrice. Si `brief` est fourni, vérifie que chaque citation y figure mot pour mot."""
    actors = {a.id: a for a in decl.actors}
    entities = {e.name: e for e in decl.entities}
    issues: list[Issue] = []
    auto_links: list[str] = []

    def err(msg: str) -> None:
        issues.append(Issue(level="error", message=msg))

    def warn(msg: str) -> None:
        issues.append(Issue(level="warning", message=msg))

    def info(msg: str) -> None:
        issues.append(Issue(level="info", message=msg))

    # ── Contrôles de cohérence de l'entrée ───────────────────────────────
    if VISITOR in actors:
        err(f"« {VISITOR} » est réservé : le visiteur existe toujours, implicitement")
    for a in decl.actors:
        if a.becomes == "invited" and a.invited_by not in actors:
            err(f"acteur {a.id} : invité par « {a.invited_by} », qui n'est pas un acteur déclaré")
    self_signup = [a.label for a in decl.actors if a.becomes == "signup"]
    if len(self_signup) > 1:
        warn(f"plusieurs acteurs s'inscrivent seuls ({', '.join(self_signup)}) : il faudrait un choix "
             "à l'inscription — hors D1")
    for e in decl.entities:
        if e.nature in ("profile", "collection") and e.owner not in actors:
            err(f"entité {e.name} ({e.nature}) : propriétaire « {e.owner} » inconnu")
        for mgr in e.managers:
            if mgr not in actors:
                err(f"entité {e.name} : gestionnaire « {mgr} » inconnu")
        if e.nature == "child" and e.parent not in entities:
            err(f"entité {e.name} (enfant) : parent « {e.parent} » inconnu")
        if e.entered_by is not None:
            if e.nature != "collection":
                err(f"entité {e.name} : « saisi par » n'a de sens que pour une collection")
            if e.entered_by not in actors:
                err(f"entité {e.name} : « saisi par » « {e.entered_by} » inconnu")
        if e.process is not None:
            p = e.process
            if e.nature != "collection":
                err(f"entité {e.name} : un processus n'est géré que sur une collection (D1)")
            for role, who in (("décideur", p.decider), ("initiateur", p.initiator), *(
                (f"étape « {s} »", a) for s, a in p.steps_by.items())):
                if who not in actors:
                    err(f"entité {e.name} : {role} « {who} » inconnu")
            if e.entered_by is not None and e.entered_by != p.initiator:
                err(f"entité {e.name} : « saisi par » ({e.entered_by}) ≠ initiateur ({p.initiator})")
            states = set(p.transitions) | {s for t in p.transitions.values() for s in t}
            if p.initial not in states:
                err(f"entité {e.name} : état initial « {p.initial} » absent des transitions")
            for s in p.steps_by:
                if not p.transitions.get(s):
                    err(f"entité {e.name} : étape « {s} » sans transition sortante")
        for r in e.references:
            if r not in entities:
                err(f"entité {e.name} : référence « {r} » inconnue")
    for x in decl.exceptions:
        if x.actor not in actors and x.actor != VISITOR:
            err(f"exception : acteur « {x.actor} » inconnu")
        if x.entity not in entities:
            err(f"exception : entité « {x.entity} » inconnue")
        if not x.citation.strip():
            err(f"exception {x.actor}/{x.entity}/{x.action} sans citation du brief")
    if brief is not None:
        nb = _norm(brief)
        cited = [(f"acteur {a.id}", a.citation) for a in decl.actors]
        cited += [(f"entité {e.name}", e.citation) for e in decl.entities]
        cited += [(f"processus {e.name}", e.process.citation) for e in decl.entities if e.process]
        cited += [(f"exception {x.actor}/{x.entity}/{x.action}", x.citation) for x in decl.exceptions]
        for who, c in cited:
            if c.strip() and _norm(c) not in nb:
                err(f"{who} : citation introuvable dans le brief — « {c} »")
    if any(i.level == "error" for i in issues):
        return Matrix(actors=[VISITOR, *actors], entities=list(entities), cells=[], issues=issues)

    # ── Grille vide ──────────────────────────────────────────────────────
    grid: dict[tuple[str, str], Cell] = {
        (a, e): Cell(actor=a, entity=e) for a in [VISITOR, *actors] for e in entities
    }

    def grant(c: Cell, why: str, *citations: str) -> None:
        c.why.append(why)
        c.sources.extend(s for s in citations if s and s not in c.sources)

    # ── 1. Préréglages des natures (moindre privilège) ───────────────────
    for e in decl.entities:
        if e.nature == "profile":
            c = grid[(e.owner, e.name)]
            c.see, c.create, c.edit = "own", "auto", True
            grant(c, "préréglage profil : sa propre fiche, créée automatiquement", e.citation)
        elif e.nature == "catalog":
            # Avec publication (brouillon / publié), les non-gestionnaires ne voient que le publié.
            reader_see = "published" if e.publication else "all"
            for a in actors:
                c = grid[(a, e.name)]
                c.see = reader_see
                grant(c, "préréglage catalogue : visible de tous les connectés"
                      + (" (publiés seulement)" if e.publication else ""), e.citation)
            if e.public:
                c = grid[(VISITOR, e.name)]
                c.see = reader_see
                grant(c, "catalogue public : visible des visiteurs"
                      + (" (publiés seulement)" if e.publication else ""), e.citation)
            for mgr in e.managers:
                c = grid[(mgr, e.name)]
                c.see, c.create, c.edit = "all", "yes", True
                grant(c, "gestionnaire du catalogue (supprimer : seulement si le brief le dit)", e.citation)
            if not e.managers:
                info(f"{e.label_plural} : catalogue en lecture seule — son contenu viendra des données de départ")
        elif e.nature == "collection" and e.process is None:
            # Supprimer n'est JAMAIS accordé par défaut (compte rendu médical, commande…) :
            # il faut une exception citant le brief (« gérer », « supprimer »).
            o = grid[(e.owner, e.name)]
            if e.entered_by and e.entered_by != e.owner:
                # Saisi pour le compte du propriétaire : celui qui saisit gère, le propriétaire suit.
                o.see = "own"
                grant(o, f"suit les {e.label_plural} saisis pour lui", e.citation)
                s = grid[(e.entered_by, e.name)]
                s.see, s.create, s.edit = "all", "yes", True
                grant(s, f"saisit les {e.label_plural} pour le compte de leur propriétaire", e.citation)
            else:
                o.see, o.create, o.edit = "own", "yes", True
                grant(o, "préréglage collection : le propriétaire crée et modifie les siens", e.citation)
        elif e.nature == "collection":
            p = e.process
            o = grid[(e.owner, e.name)]
            o.see = "own"
            if p.initiator == e.owner:
                o.create = "yes"
                grant(o, "préréglage collection + processus : l'initiateur crée et suit les siens", e.citation)
            else:
                grant(o, f"suit les {e.label_plural} créés pour lui", e.citation)
                i = grid[(p.initiator, e.name)]
                i.see, i.create = "all", "yes"
                grant(i, f"crée les {e.label_plural} pour le compte de leur propriétaire", p.citation)
            # Le décideur fait toutes les étapes, sauf celles confiées à un autre acteur (steps_by).
            d = grid[(p.decider, e.name)]
            d.transitions = {s: list(t) for s, t in p.transitions.items() if t and s not in p.steps_by}
            if p.decider != e.owner:
                d.see = "all"
                grant(d, "décideur du processus : voit tout et fait évoluer l'état", p.citation)
            else:
                grant(d, "le propriétaire fait évoluer l'état de ses propres éléments", p.citation)
            for s, who in p.steps_by.items():
                w = grid[(who, e.name)]
                w.transitions[s] = list(p.transitions[s])
                if who != e.owner and w.see == "none":
                    w.see = "all"
                grant(w, f"fait l'étape depuis « {s} »", p.citation)
        if e.nature == "collection" and e.public:
            # Collection publique (produits d'un vendeur, annonces) : chacun gère les siens,
            # tout le monde — visiteur compris — les voit tous.
            for a in [VISITOR, *actors]:
                if a != e.owner and grid[(a, e.name)].see == "none":
                    c = grid[(a, e.name)]
                    c.see = "all"
                    grant(c, "collection publique : visible de tous", e.citation)

    # ── 2. Enfants : héritent de la visibilité du parent ─────────────────
    # (après les préréglages des parents ; un seul niveau en D1). Moindre privilège :
    #  - le visiteur n'hérite PAS : un enfant n'est public que s'il est déclaré public
    #    (les participants d'une sortie publique ne le sont pas — fuite réelle du 6 juillet) ;
    #  - seul qui peut MODIFIER le parent gère ses enfants (créer un parent ne suffit pas :
    #    le membre qui réserve ne crée pas ses factures).
    for e in decl.entities:
        if e.nature != "child":
            continue
        for a in [VISITOR, *actors]:
            pc, c = grid[(a, e.parent)], grid[(a, e.name)]
            if a == VISITOR and not e.public:
                continue
            c.see = pc.see
            if pc.edit:
                c.create, c.edit = "yes", True
            if pc.see != "none":
                grant(c, f"enfant de {entities[e.parent].label} : même visibilité que le parent"
                      + (", géré par qui gère le parent" if pc.edit else ""), *pc.sources)

    # ── 3. Exceptions citées ─────────────────────────────────────────────
    for x in decl.exceptions:
        c = grid[(x.actor, x.entity)]
        c.sources.append(x.citation)
        tag = f"exception : « {x.citation} »"
        if x.action == "see":
            c.see = x.scope if x.allow else "none"
        elif x.action == "create":
            c.create = "yes" if x.allow else "no"
        elif x.action == "edit":
            c.edit, c.edit_while = x.allow, (list(x.while_states) if x.allow else [])
        elif x.action == "delete":
            c.delete, c.delete_while = x.allow, (list(x.while_states) if x.allow else [])
        elif x.action == "transition":
            if x.allow:
                for s, t in x.transitions.items():
                    c.transitions[s] = sorted(set(c.transitions.get(s, [])) | set(t))
            else:
                for s, t in x.transitions.items():
                    c.transitions[s] = [v for v in c.transitions.get(s, []) if v not in t]
                c.transitions = {s: t for s, t in c.transitions.items() if t}
        c.why.append(tag)

    # ── 4. Clôture ───────────────────────────────────────────────────────
    def creator(e: Entity) -> str | None:
        if e.nature != "collection":
            return None
        return e.process.initiator if e.process else (e.entered_by or e.owner)

    for e in decl.entities:
        for r in e.references:
            ref = entities[r]
            owners_profile = ref.nature == "profile" and e.owner is not None and ref.owner == e.owner
            # a) Le propriétaire crée lui-même : le lien vers SA fiche est rempli automatiquement.
            auto = owners_profile and creator(e) == e.owner
            if auto:
                auto_links.append(f"{e.label} → {ref.label} : rempli automatiquement avec la fiche de l'acteur")
            # b) Quelqu'un crée POUR le propriétaire : il doit pouvoir choisir pour qui.
            if owners_profile and creator(e) not in (None, e.owner):
                cc = grid[(creator(e), r)]
                if cc.see in ("none",):
                    cc.see = "all"
                    grant(cc, f"clôture : choisit pour qui il saisit les {e.label_plural}", e.citation)
            for a in [VISITOR, *actors]:
                c, rc = grid[(a, e.name)], grid[(a, r)]
                # c) Qui voit un élément voit ce qu'il référence, DANS sa fiche (see_via) —
                #    pas le droit de parcourir l'entité référencée, qui resterait un désir.
                if c.see != "none" and rc.see == "none" and e.name not in rc.see_via:
                    rc.see_via.append(e.name)
                    rc.why.append(f"clôture : affiché dans les {e.label_plural} qu'il voit")
                # d) Qui crée doit pouvoir choisir ce que l'élément référence (sauf lien automatique).
                if a != VISITOR and c.create == "yes" and rc.see == "none" and not (auto and a == e.owner):
                    warn(f"{actors[a].label} crée des {e.label_plural} qui référencent des "
                         f"{ref.label_plural}, mais n'en voit aucun : impossible de choisir (D2 ?)")

    # ── 5. Contrôles de la matrice obtenue ───────────────────────────────
    for a in decl.actors:
        if all(grid[(a.id, e)].see == "none" for e in entities):
            warn(f"l'acteur {a.label} ne voit rien : rôle inutile ou déclaration incomplète")
        if a.becomes == "invited":
            inviter = actors[a.invited_by]
            info(f"page « Équipe » pour {inviter.label} : inviter des {a.label_plural or a.label + 's'}")
    for e in decl.entities:
        if e.nature in ("collection", "child") and not any(
            grid[(a, e.name)].create != "no" for a in [VISITOR, *actors]
        ):
            warn(f"personne ne peut créer de {e.label_plural}")

    return Matrix(
        actors=[VISITOR, *actors],
        entities=list(entities),
        cells=list(grid.values()),
        auto_links=auto_links,
        issues=issues,
    )


# ══════════════════════════════════════════════════════════════════════════
# Dérivés : pages, navigation, tableaux de bord
# ══════════════════════════════════════════════════════════════════════════

class Page(BaseModel):
    entity: str
    kind: Literal["profile", "list", "detail", "create", "edit", "team"]
    actors: list[str]
    decision_by: list[str] = Field(default_factory=list)   # fiche : qui y voit le bloc de décision


def derive_pages(m: Matrix, decl: AccessDeclaration) -> list[Page]:
    entities = {e.name: e for e in decl.entities}
    pages: list[Page] = []
    for name in m.entities:
        cells = [m.cell(a, name) for a in m.actors]
        if entities[name].nature == "profile":
            owners = [c.actor for c in cells if c.see == "own"]
            if owners:
                pages.append(Page(entity=name, kind="profile", actors=owners))
            continue
        viewers = [c.actor for c in cells if c.see != "none"]
        if not viewers:
            continue
        deciders = [c.actor for c in cells if c.transitions]
        pages.append(Page(entity=name, kind="list", actors=viewers))
        pages.append(Page(entity=name, kind="detail", actors=viewers, decision_by=deciders))
        creators = [c.actor for c in cells if c.create == "yes"]
        if creators:
            pages.append(Page(entity=name, kind="create", actors=creators))
        editors = [c.actor for c in cells if c.edit]
        if editors:
            pages.append(Page(entity=name, kind="edit", actors=editors))
    inviters = sorted({a.invited_by for a in decl.actors if a.becomes == "invited"})
    if inviters:
        pages.append(Page(entity="", kind="team", actors=inviters))
    return pages


def derive_nav(m: Matrix, decl: AccessDeclaration) -> dict[str, list[str]]:
    """Par acteur : entrées de menu ordonnées (à traiter → les miens → catalogues → mon profil)."""
    entities = {e.name: e for e in decl.entities}
    nav: dict[str, list[str]] = {}
    for a in m.actors:
        decide, mine, shared, profile = [], [], [], []
        for name in m.entities:
            c, e = m.cell(a, name), entities[name]
            if c.see == "none" or e.nature == "child":
                continue
            if e.nature == "profile":
                profile.append(f"{'Ma' if e.feminine else 'Mon'} {e.label}")
            elif c.transitions and c.see == "all":
                decide.append(f"{e.label_plural.capitalize()} à traiter")
            elif c.see == "own":
                mine.append(f"Mes {e.label_plural}")
            else:
                shared.append(e.label_plural.capitalize())
        team = ["Équipe"] if any(x.becomes == "invited" and x.invited_by == a for x in decl.actors) else []
        nav[a] = decide + mine + shared + team + profile
    return nav


def derive_dashboards(m: Matrix, decl: AccessDeclaration) -> dict[str, list[str]]:
    """Par acteur connecté : « à traiter » (états où il peut agir) puis « en cours » (les siens)."""
    entities = {e.name: e for e in decl.entities}
    dash: dict[str, list[str]] = {}
    for a in m.actors:
        if a == VISITOR:
            continue
        blocks: list[str] = []
        for name in m.entities:
            c, e = m.cell(a, name), entities[name]
            if c.transitions:
                states = ", ".join(_state(e, s) for s in c.transitions)
                blocks.append(f"À traiter : {e.label_plural} {states}")
        for name in m.entities:
            c, e = m.cell(a, name), entities[name]
            if c.see == "own" and e.process is not None:
                terminal = {s for s, t in e.process.transitions.items() if not t}
                states = [s for s in e.process.transitions if s not in terminal]
                blocks.append(f"Mes {e.label_plural} en cours ({', '.join(_state(e, s) for s in states)})")
        dash[a] = blocks
    return dash


# ══════════════════════════════════════════════════════════════════════════
# Miroir : phrases déterministes et questions ciblées
# ══════════════════════════════════════════════════════════════════════════

def the(label: str) -> str:
    """« le bibliothécaire », « l'adhérent » (élision devant voyelle ou h)."""
    return f"l'{label}" if label[:1].lower() in "aeiouyhéèêàâîôû" else f"le {label}"


def _state(e: Entity, s: str) -> str:
    return f"« {e.process.labels.get(s, s) if e.process else s} »"


def explain(m: Matrix, decl: AccessDeclaration) -> dict[str, list[str]]:
    """« Qui peut faire quoi », en phrases, par acteur. Produit par du code : ne peut pas mentir
    sur la matrice."""
    labels = {a.id: a.label for a in decl.actors}
    labels[VISITOR] = "visiteur"
    entities = {e.name: e for e in decl.entities}
    out: dict[str, list[str]] = {}
    for a in m.actors:
        lines = []
        for name in m.entities:
            c, e = m.cell(a, name), entities[name]
            pron = "elles" if e.feminine else "ils"
            if c.see == "none":
                if c.see_via:
                    via = " et les ".join(entities[v].label_plural for v in c.see_via)
                    lines.append(f"voit les {e.label_plural} affiché{'e' if e.feminine else ''}s "
                                 f"dans les {via} qu'il consulte (sans page dédiée)")
                continue
            if e.nature == "profile":
                lines.append(f"a {'sa' if e.feminine else 'son'} {e.label}, "
                             f"créé{'e' if e.feminine else ''} automatiquement, qu'il peut modifier")
                continue
            everyone = "toutes les" if e.feminine else "tous les"
            seen = {
                "all": f"{everyone} {e.label_plural}",
                "own": f"ses {e.label_plural}",
                "published": f"les {e.label_plural} publié{'e' if e.feminine else ''}s",
            }[c.see]
            parts = [f"voit {seen}"]
            if c.create == "yes":
                parts.append("en crée")
            if c.edit:
                parts.append("les modifie" + (f" tant qu'{pron} sont " + " ou ".join(_state(e, s) for s in c.edit_while) if c.edit_while else ""))
            if c.delete:
                parts.append("les supprime" + (f" tant qu'{pron} sont " + " ou ".join(_state(e, s) for s in c.delete_while) if c.delete_while else ""))
            for s, t in c.transitions.items():
                parts.append(f"les fait passer de {_state(e, s)} à " + " ou ".join(_state(e, v) for v in t))
            lines.append(", ".join(parts))
        out[the(labels[a]).capitalize()] = lines or ["ne voit rien"]
    return out


def questions(m: Matrix, decl: AccessDeclaration) -> list[str]:
    """Questions oui/non à poser au client, seulement là où une erreur coûte ET que le brief ne
    tranche pas : un acteur qui voit les données d'un autre sans citation qui le justifie, ou un
    droit déduit par une règle de clôture."""
    labels = {a.id: a.label for a in decl.actors}
    entities = {e.name: e for e in decl.entities}
    qs = []
    for c in m.cells:
        e = entities[c.entity]
        if c.actor == VISITOR:
            # Ce que voit un visiteur sans compte : la question vaut toujours d'être posée
            # (test de l'IA du 1er oct : l'erreur réelle était des brouillons rendus publics).
            if c.see == "all":
                every, those, ready, pub = (("toutes les", "celles", "prêtes", "publiées") if e.feminine
                                            else ("tous les", "ceux", "prêts", "publiés"))
                qs.append(f"Les visiteurs sans compte verront {every} {e.label_plural}, y compris "
                          f"{those} qui ne sont pas {ready} ou pas {pub} — d'accord ? (oui / non)")
            continue
        owner = e.owner if e.nature != "child" else entities[e.parent].owner if e.parent else None
        who = the(labels[c.actor]).capitalize()
        if c.see == "all" and e.nature in ("collection", "child") and owner and owner != c.actor and not c.sources:
            qs.append(f"{who} doit-il voir les {e.label_plural} de tout le monde ? (oui / non)")
        if c.see_via and owner != c.actor:
            via = " et les ".join(entities[v].label_plural for v in c.see_via)
            qs.append(f"{who} verra les {e.label_plural} (ex. nom, coordonnées) affichés "
                      f"dans les {via} qu'il traite — est-ce acceptable ? (oui / non)")
    return list(dict.fromkeys(qs))
