"""
agents/dev_prisma_extractor.py
───────────────────────────────
Extrait le Type Map réel depuis node_modules/.prisma/client/index.d.ts
après un `npx prisma generate` réussi.

Pourquoi : lib/types.ts est généré depuis ProjectSpec, mais @prisma/client génère
ses propres signatures. En injectant le Type Map extrait, l'agent Dev voit les
types RÉELS produits par Prisma (PascalCase exact, Enum string values, nullable fields)
plutôt que notre reconstruction.

Résultat : dict{ ModelName → PrismaTypeEntry } injecté dans DevState.prisma_type_map.
Exemple :
  {
    "Project": {
        "model_type": "export type Project = { id: string; title: string; ... }",
        "create_input": "export type ProjectCreateInput = { ... }",
        "where_input": "export type ProjectWhereInput = { ... }",
    },
    ...
  }
"""
from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)

# Limite de caractères par entrée pour ne pas exploser le contexte LLM
_MAX_CHARS_PER_ENTRY = 600


def _extract_block(text: str, start_offset: int) -> str:
    """Extrait le bloc {...} ou = ... démarrant à start_offset (après 'type X = ')."""
    depth = 0
    i = start_offset
    n = len(text)
    in_block = False
    start = -1

    while i < n:
        ch = text[i]
        if ch == "{":
            if not in_block:
                in_block = True
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and in_block:
                return text[start: i + 1]
        elif ch == ";" and not in_block:
            # type X = Y; forme simple sans bloc
            return text[start_offset: i + 1] if start == -1 else text[start: i + 1]
        i += 1
    return ""


def extract_prisma_type_map(project_workdir: str) -> dict[str, dict[str, str]]:
    """
    Lit node_modules/.prisma/client/index.d.ts et extrait les déclarations de type
    pour chaque modèle : modèle principal, CreateInput, WhereInput.

    Retourne un dict vide si le fichier n'existe pas (prisma generate non encore lancé).
    """
    dts_path = os.path.join(
        project_workdir, "node_modules", ".prisma", "client", "index.d.ts"
    )
    if not os.path.exists(dts_path):
        logger.warning("[prisma_extractor] index.d.ts absent — prisma generate non encore lancé")
        return {}

    try:
        with open(dts_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error("[prisma_extractor] Lecture échouée : %s", e)
        return {}

    result: dict[str, dict[str, str]] = {}

    # Détecter les noms de modèles déclarés (export type ModelName = {)
    model_names: set[str] = set()
    for m in re.finditer(r"\nexport type ([A-Z][A-Za-z0-9]+) = \{", content):
        name = m.group(1)
        # Exclure les types utilitaires Prisma (PrismaClient, etc.)
        if not any(
            suffix in name
            for suffix in (
                "Args", "Payload", "Delegate", "Client", "Promise",
                "Unchecked", "Default", "GetHaving", "GetResult",
                "AggregateRaw", "GetScalar",
            )
        ):
            model_names.add(name)

    for model in model_names:
        entry: dict[str, str] = {}

        # 1. Type principal du modèle (ex: export type Project = {...})
        pat_model = re.compile(
            rf"\nexport type {re.escape(model)} = (\{{[^;]*?}})", re.DOTALL
        )
        m_model = pat_model.search(content)
        if m_model:
            block = m_model.group(0).strip()
            entry["model_type"] = block[:_MAX_CHARS_PER_ENTRY]

        # 2. CreateInput
        for suffix in (f"{model}CreateInput", f"{model}UncheckedCreateInput"):
            idx = content.find(f"\nexport type {suffix} = {{")
            if idx != -1:
                snippet = content[idx: idx + _MAX_CHARS_PER_ENTRY]
                entry["create_input"] = snippet.strip()
                break

        # 3. UpdateInput
        for suffix in (f"{model}UpdateInput", f"{model}UncheckedUpdateInput"):
            idx = content.find(f"\nexport type {suffix} = {{")
            if idx != -1:
                snippet = content[idx: idx + _MAX_CHARS_PER_ENTRY]
                entry["update_input"] = snippet.strip()
                break

        # 4. WhereInput (utile pour relations et filtres)
        idx_where = content.find(f"\nexport type {model}WhereInput = {{")
        if idx_where != -1:
            snippet = content[idx_where: idx_where + _MAX_CHARS_PER_ENTRY]
            entry["where_input"] = snippet.strip()

        if entry:
            result[model] = entry
            logger.debug("[prisma_extractor] ✓ %s (%d entrées)", model, len(entry))

    logger.info("[prisma_extractor] Type Map extrait : %d modèles", len(result))
    return result


def format_type_map_for_prompt(type_map: dict[str, dict[str, str]]) -> str:
    """
    Formatte le Type Map en bloc Markdown injectable dans le prompt LLM.
    Budget : ~200 chars par modèle (model_type tronqué) pour rester sous 2000 chars total.
    """
    if not type_map:
        return ""

    lines = ["### Prisma Type Map (types RÉELS générés par @prisma/client)\n"]
    for model, entry in sorted(type_map.items()):
        lines.append(f"**{model}**")
        if "model_type" in entry:
            # Première ligne du type suffit comme référence rapide
            first_line = entry["model_type"].split("\n")[0]
            lines.append(f"  Type : `{first_line[:120]}`")
        if "create_input" in entry:
            first_line = entry["create_input"].split("\n")[0]
            lines.append(f"  Create : `{first_line[:120]}`")
        lines.append("")

    return "\n".join(lines)
