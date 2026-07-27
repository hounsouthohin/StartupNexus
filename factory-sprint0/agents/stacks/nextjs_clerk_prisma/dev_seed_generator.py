"""
dev_seed_generator.py — données de démonstration pour le PREVIEW local (23 Juil 2026).
─────────────────────────────────────────────────────────────────────────────────────

Produit `prisma/seed.ts` : 2 lignes réalistes par modèle, écrites DIRECTEMENT via Prisma
(donc sans passer par les services — on écrit le slug, l'état initial, etc. à la main).

But : que l'opérateur (et le client) voient une app PEUPLÉE, pas des pages vides, en
la lançant en local. C'est la brique déterministe de la Scène-B.

Il travaille sur le système de types de Prisma (FERMÉ : String/Int/Float/Decimal/Boolean/
DateTime/enum/FK) — donc il ne s'étend PAS par type d'app, seulement sur un nouveau motif
STRUCTUREL (ex: M2M connect, multi-acteur). Dev-only → un bug de seed ne casse jamais un build.

Contraintes respectées :
  • ordre des FK    : un parent est créé avant ses enfants (tri topologique) ;
  • machine à états : le champ status prend `status_flow.initial` (jamais un état avancé) ;
  • enums           : première valeur autorisée ;
  • owner (userId)  : `process.env.SEED_USER_ID ?? 'user_demo'` — l'opérateur y met son
                      propre id Clerk pour que les données lui appartiennent (sinon elles
                      sont filtrées par le owner-guard des services).
"""
from __future__ import annotations

import os

from .dev_model_context import ModelGenerationContext

_SEED_ROWS = 2  # lignes par modèle — assez pour voir des listes non vides


def _is_auto(name: str, attributes: str) -> bool:
    n = name.lower()
    if n in ("id", "createdat", "updatedat", "deletedat"):
        return True
    a = (attributes or "").lower().replace(" ", "")
    return "@id" in a or "@default(now())" in a or "@updatedat" in a


def _ts_value(ctx: ModelGenerationContext, field, i: int) -> str:
    """Littéral TypeScript pour UN champ scalaire (jamais owner/FK/relation)."""
    name = field.name
    base = field.type.rstrip("?").rstrip("[]")
    nlow = name.lower()

    # Machine à états : toujours l'état INITIAL, jamais un état avancé.
    _flow = getattr(ctx, "status_flow", None)
    if _flow is not None and name == _flow.field:
        return repr(_flow.initial)

    # Enum Prisma → première valeur autorisée.
    _enum_vals = (ctx.spec_enums or {}).get(base) or []
    if _enum_vals:
        return repr(_enum_vals[0])

    if base == "Boolean":
        return "true" if i % 2 == 0 else "false"
    if base in ("Int", "BigInt"):
        return str(10 * (i + 1))
    if base in ("Float", "Decimal"):
        return f"{42.5 * (i + 1):.2f}"
    if base == "DateTime":
        return f"new Date(Date.now() + {i} * 86400000)"

    # String — quelques cas sémantiques utiles, sinon libellé indexé.
    if "email" in nlow:
        return repr(f"demo{i + 1}@example.com")
    if nlow == "slug":
        return repr(f"exemple-{ctx.camel}-{i + 1}")
    if "url" in nlow or "link" in nlow:
        return repr(f"https://example.com/{ctx.camel}/{i + 1}")
    if any(k in nlow for k in ("description", "content", "body", "notes", "message")):
        return repr(f"Contenu de démonstration pour {ctx.name} n°{i + 1}.")
    # Libellé basé sur le NOM DU CHAMP → des valeurs distinctes d'un champ à l'autre.
    return repr(f"{name[0].upper() + name[1:]} exemple {i + 1}")


def _topo_order(contexts: dict[str, ModelGenerationContext]) -> list[str]:
    """Ordonne les modèles : un parent (référencé par FK) avant ses enfants."""
    known = set(contexts)
    remaining = set(contexts)
    ordered: list[str] = []
    while remaining:
        progressed = False
        for name in list(remaining):
            parents = {fk.related_model for fk in (contexts[name].fk_fields or [])} & known
            if parents <= set(ordered):  # tous les parents connus sont déjà placés
                ordered.append(name)
                remaining.discard(name)
                progressed = True
        if not progressed:  # cycle → on place le reste tel quel
            ordered.extend(sorted(remaining))
            break
    return ordered


def _model_block(ctx: ModelGenerationContext, contexts: dict, multi_actor: bool = False) -> list[str]:
    """Lignes TS créant les _SEED_ROWS lignes d'un modèle."""
    lines: list[str] = []
    fk_by_field = {fk.field_name: fk for fk in (ctx.fk_fields or [])}
    m2m_names = {mf.name for mf in (getattr(ctx, "m2m_fields", []) or [])}
    # Champs liés à une transition (ex: rejectionReason au refus) : ils n'ont de sens
    # qu'à leur état, pas au démarrage. Une note 'draft' semée avec un motif de refus
    # serait incohérente — on les laisse vides, comme le fait le formulaire de création.
    _flow = getattr(ctx, "status_flow", None)
    _state_fields = set(_flow.all_state_fields()) if _flow is not None else set()
    _is_global = getattr(ctx, "is_global", False)

    for i in range(_SEED_ROWS):
        # K6 — entité globale : aucun owner (le champ n'existe pas dans le modèle).
        # K8 — app multi-acteur : on répartit les lignes possédées entre DEUX owners
        # (OWNER / OWNER2) pour que « admin voit tout » montre bien les données de
        # plusieurs personnes, pas une seule. L'alternance est par indice de ligne :
        # parent[i] et enfant[i] partagent donc le même owner (FK-owner cohérente).
        if _is_global:
            assigns: list[str] = []
        elif multi_actor:
            assigns = [f"{ctx.owner}: {'OWNER' if i % 2 == 0 else 'OWNER2'}"]
        else:
            assigns = [f"{ctx.owner}: OWNER"]
        for f in ctx.model.fields:
            name = f.name
            if name == ctx.owner or name == "id":
                continue
            if _is_auto(name, getattr(f, "attributes", "")):
                continue
            if "@relation" in (getattr(f, "attributes", "") or "") or f.type.endswith("[]"):
                continue  # objet relation / M2M — géré via la FK scalaire, ou ignoré
            # Champ-relation SANS @relation : le côté inverse d'un 1-1 (`invoice Invoice?`)
            # a pour type un MODÈLE, pas un scalaire. Le semer comme String produirait
            # `invoice: 'Invoice exemple 1'` → crash Prisma au runtime (constaté coworking 26 Juil).
            if f.type.rstrip("?").rstrip("[]") in contexts:
                continue
            if name in m2m_names or name in _state_fields:
                continue
            if name in fk_by_field:
                fk = fk_by_field[name]
                if fk.related_model in contexts:
                    _pidx = min(i, _SEED_ROWS - 1)
                    assigns.append(f"{name}: {fk.related_camel}Rows[{_pidx}].id")
                continue
            assigns.append(f"{name}: {_ts_value(ctx, f, i)}")
        lines.append(
            f"  {ctx.camel}Rows.push(await prisma.{ctx.camel}.create({{ data: {{ {', '.join(assigns)} }} }}))"
        )
    return lines


def generate_seed_file(spec, project_workdir: str, contexts: dict | None = None) -> dict[str, str]:
    """Écrit prisma/seed.ts. Retourne {rel_path: content} (vide si pas de contextes)."""
    if not contexts:
        return {}

    # K8 — l'app est multi-acteur si au moins un modèle a un rôle privilégié déclaré.
    # Alors on sème deux owners pour que « admin voit tout » soit démontrable en preview.
    multi_actor = any(getattr(c, "privileged_role", "") for c in contexts.values())

    order = _topo_order(contexts)
    header = [
        "// AUTO-GÉNÉRÉ PAR dev_seed_generator.py — données de démonstration (Preview local).",
        "// JS pur (.mjs) → lancé par `node prisma/seed.mjs`, sans tsx ni build. Dev-only.",
        "// Lancer : DATABASE_URL=... SEED_USER_ID=<votre-id-clerk> node prisma/seed.mjs",
        "// Prisma 7 exige un driver adapter (comme lib/prisma.ts) — un new PrismaClient() nu échoue.",
        "import { PrismaClient } from '@prisma/client'",
        "import { PrismaPg } from '@prisma/adapter-pg'",
        "import { Pool } from 'pg'",
        "",
        "const pool = new Pool({ connectionString: process.env.DATABASE_URL })",
        "const adapter = new PrismaPg(pool)",
        "const prisma = new PrismaClient({ adapter })",
        "const OWNER = process.env.SEED_USER_ID ?? 'user_demo'",
    ]
    if multi_actor:
        # Deuxième acteur : ses données appartiennent à un AUTRE membre. L'admin (OWNER,
        # rôle=admin dans Clerk) les verra via getAllAsAdmin ; un membre ne verrait que les siennes.
        header.append("const OWNER2 = process.env.SEED_USER_ID_2 ?? 'user_demo_2'")
    header += ["", "async function main() {"]

    body: list[str] = []
    for name in order:
        ctx = contexts[name]
        body.append(f"  const {ctx.camel}Rows = []")  # JS pur : pas d'annotation de type
        body += _model_block(ctx, contexts, multi_actor=multi_actor)
        body.append("")
    footer = [
        "  console.log('Seed termine pour l utilisateur', OWNER)",
        "}",
        "",
        "main()",
        "  .catch((e) => { console.error(e); process.exit(1) })",
        "  .finally(async () => { await prisma.$disconnect(); await pool.end() })",
        "",
    ]
    content = "\n".join(header + body + footer)

    abs_path = os.path.join(project_workdir, "prisma", "seed.mjs")
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"prisma/seed.mjs": content}
