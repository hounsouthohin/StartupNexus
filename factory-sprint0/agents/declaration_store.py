"""
Conservation de la déclaration — USINE.md, principe 7 : « la déclaration est le produit ».

La déclaration = le ProjectSpec complet produit par l'architect (modèles, pages, pages_detail,
enriched_spec, design_system, miroir summary_fr/unsupported) + le brief d'origine. Le champ
`project_spec` est EXACTEMENT le dict que dev_graph reçoit : le rejouer reproduit la
génération déterministe (voir scripts/harness.py).

Emplacements :
  - logs/declarations/<projet>/<horodatage>.json : chaque run, écrit par l'architect (historique)
  - harness/declarations/<projet>.json            : étalons choisis, rejoués par le harnais
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

FORMAT = "factory-declaration/v1"

_ROOT = Path(__file__).resolve().parent.parent


def declarations_dir() -> Path:
    """Dossier de l'historique des déclarations (monté sur l'hôte via ./logs)."""
    return Path(os.getenv("FACTORY_DECLARATIONS_DIR") or (_ROOT / "logs" / "declarations"))


def build_declaration(
    project_name: str,
    brief: dict,
    project_spec: dict,
    run_id: str = "",
    stack_id: str = "",
) -> dict:
    return {
        "format": FORMAT,
        "project_name": project_name,
        "stack_id": stack_id or project_spec.get("stack_id", ""),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": run_id,
        "brief": brief,
        "project_spec": project_spec,
    }


def save_declaration(declaration: dict, dest: Path | str | None = None) -> Path:
    """Écrit la déclaration. Sans `dest` : logs/declarations/<projet>/<horodatage>_<run>.json."""
    if dest is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run = (declaration.get("run_id") or "")[:8]
        name = f"{stamp}_{run}.json" if run else f"{stamp}.json"
        dest = declarations_dir() / declaration["project_name"] / name
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(declaration, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return dest


def load_declaration(path: Path | str) -> dict:
    """Lit une déclaration et vérifie sa forme (refus explicite, jamais de lecture partielle)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise ValueError(f"{path} : format de déclaration inconnu (attendu {FORMAT})")
    if not isinstance(data.get("project_spec"), dict) or not data["project_spec"].get("models"):
        raise ValueError(f"{path} : project_spec absent ou sans modèles")
    if not data.get("project_name"):
        raise ValueError(f"{path} : project_name absent")
    return data
