"""
agents/dev_prisma_extractor.py
───────────────────────────────
Extrait le Type Map réel depuis le DMMF Prisma (Data Model Meta Format).

Approche : Node.js subprocess `require('@prisma/client').Prisma.dmmf` — garanti
d'être exact peu importe la version Prisma, contrairement aux regex sur index.d.ts
dont le format change à chaque release majeure.

Résultat : dict{ ModelName → list[FieldInfo] } injecté dans le system prompt.
Exemple :
  {
    "LeaveRequest": [
      {"name": "startDate", "type": "DateTime", "isRequired": True, "hasDefault": False,
       "isRelation": False, "isId": False, "isUpdatedAt": False},
      ...
    ],
  }
"""
from __future__ import annotations

import json
import logging
import subprocess
import os

logger = logging.getLogger(__name__)

# Script Node.js inline — lit le DMMF et produit du JSON sur stdout
_DMMF_SCRIPT = r"""
try {
  var p = require('@prisma/client');
  var dmmf = p.Prisma.dmmf;
  var models = dmmf.datamodel.models;
  var result = {};
  models.forEach(function(m) {
    result[m.name] = m.fields.map(function(f) {
      return {
        name: f.name,
        type: f.type,
        isRequired: f.isRequired === true && f.isNullable !== true,
        hasDefault: f.hasDefault === true || f.default !== undefined,
        isRelation: !!f.relationName,
        isId: !!f.isId,
        isUpdatedAt: !!f.isUpdatedAt
      };
    });
  });
  console.log(JSON.stringify(result));
} catch(e) {
  process.stderr.write('DMMF_ERROR: ' + e.message + '\n');
  process.exit(1);
}
"""


def extract_prisma_type_map(project_workdir: str) -> dict[str, list[dict]]:
    """
    Appelle Node.js pour lire le DMMF de @prisma/client et retourne la structure
    de chaque modèle avec les types réels de ses champs.

    Retourne un dict vide si @prisma/client n'est pas installé ou si prisma generate
    n'a pas encore été lancé.
    """
    # Vérifie qu'on a bien un @prisma/client disponible
    client_dir = os.path.join(project_workdir, "node_modules", "@prisma", "client")
    prisma_dir = os.path.join(project_workdir, "node_modules", ".prisma", "client")
    if not os.path.isdir(client_dir) and not os.path.isdir(prisma_dir):
        logger.warning(
            "[prisma_extractor] @prisma/client absent dans %s — prisma generate non lancé",
            project_workdir,
        )
        return {}

    try:
        proc = subprocess.run(
            ["node", "-e", _DMMF_SCRIPT],
            cwd=project_workdir,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        logger.warning("[prisma_extractor] node non trouvé dans PATH")
        return {}
    except subprocess.TimeoutExpired:
        logger.warning("[prisma_extractor] timeout DMMF extraction")
        return {}
    except Exception as e:
        logger.warning("[prisma_extractor] subprocess error : %s", e)
        return {}

    if proc.returncode != 0:
        logger.warning(
            "[prisma_extractor] node DMMF script échec (rc=%d) : %s",
            proc.returncode,
            proc.stderr[:300],
        )
        return {}

    stdout = proc.stdout.strip()
    if not stdout:
        logger.warning("[prisma_extractor] DMMF script stdout vide")
        return {}

    try:
        raw: dict[str, list[dict]] = json.loads(stdout)
    except json.JSONDecodeError as e:
        logger.warning("[prisma_extractor] JSON invalide : %s — début : %r", e, stdout[:200])
        return {}

    logger.info("[prisma_extractor] DMMF extrait : %d modèles — %s", len(raw), list(raw.keys()))
    return raw


def format_type_map_for_prompt(type_map: dict[str, list[dict]]) -> str:
    """
    Formatte le DMMF en bloc Markdown injectable dans le system prompt.

    Objectif : donner au LLM une vue actionnable des champs de chaque modèle,
    en particulier :
      - Champs DateTime requis → new Date(value) obligatoire dans le service
      - Champs requis sans défaut → présents dans CreateInput
      - Relations → disponibles pour prisma include

    Format compact : ~150 chars par modèle pour rester sous 2 000 chars total.
    """
    if not type_map:
        return ""

    lines: list[str] = [
        "══════════════════════════════════════════════════════════════",
        "TYPES PRISMA RÉELS (DMMF — source de vérité)",
        "══════════════════════════════════════════════════════════════",
    ]

    for model_name, fields in sorted(type_map.items()):
        # Champs requis sans défaut ET non-relation ET non-id (→ dans CreateInput)
        create_fields = [
            f for f in fields
            if f.get("isRequired")
            and not f.get("hasDefault")
            and not f.get("isRelation")
            and not f.get("isId")
            and not f.get("isUpdatedAt")
        ]

        # Parmi ceux-là, les DateTime (→ doivent recevoir new Date() dans le service)
        datetime_required = [f for f in create_fields if f["type"] == "DateTime"]

        # Relations (→ disponibles pour include)
        relation_fields = [f["name"] for f in fields if f.get("isRelation")]

        # Champs optionnels non-relation (pour UpdateInput)
        optional_non_relation = [
            f for f in fields
            if not f.get("isRequired")
            and not f.get("isRelation")
            and not f.get("isId")
            and not f.get("isUpdatedAt")
        ]

        model_lines: list[str] = [f"\n▶ {model_name}"]

        if create_fields:
            create_names = ", ".join(
                f"{f['name']}:{f['type']}" for f in create_fields
            )
            model_lines.append(f"  Requis dans Create : {create_names}")

        if datetime_required:
            dt_names = ", ".join(f["name"] for f in datetime_required)
            model_lines.append(
                f"  ⚠ DateTime requis (z.coerce.date() coerce string→Date) : {dt_names}"
                f" — sérialiser pour JSX : .toISOString()"
            )

        if optional_non_relation:
            opt_names = ", ".join(
                f"{f['name']}:{f['type']}" for f in optional_non_relation
            )
            model_lines.append(f"  Optionnels (Update) : {opt_names}")

        if relation_fields:
            model_lines.append(f"  Relations include : {', '.join(relation_fields)}")

        lines.extend(model_lines)

    lines.append("")
    return "\n".join(lines)
