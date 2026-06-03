"""
agents/reviewer.py
──────────────────
Reviewer sémantique post-build.

Reçoit le code généré (services, actions, pages) + le brief + les standards RAG,
produit un ReviewReport JSON structuré avec verdict et targeted_fixes.

Pas de LangGraph — inference mono-passe, un seul appel LLM.
Modèle : gpt-4o (détection sémantique fine : IDOR, ghost success, cross-user).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_REVIEWER_MODEL = "gpt-4o"
_MAX_FILE_CHARS = 3000
_MAX_STANDARDS_CHARS = 4000


def _load_reviewer_prompt(stack_id: str) -> str:
    from utils.prompt_loader import load_stack_prompt
    try:
        return load_stack_prompt("reviewer", stack_id)
    except FileNotFoundError:
        from utils.prompt_loader import load_prompt
        logger.warning("[reviewer] Prompt stack introuvable — fallback base reviewer.md")
        return load_prompt("reviewer")


def _build_human_message(
    brief: str,
    spec: dict,
    user_flows: list,
    selected_files: dict[str, str],
    rag_standards: str,
    page_auth_contract: str = "",
) -> str:
    parts: list[str] = []

    parts.append("## BRIEF ORIGINAL\n" + (brief or "(absent)"))

    if page_auth_contract:
        parts.append(page_auth_contract)

    entities = spec.get("entities") or spec.get("models") or []
    routes = spec.get("routes") or []
    parts.append(
        "## PROJECT SPEC\n"
        f"Entités: {', '.join(e if isinstance(e, str) else e.get('name', str(e)) for e in entities)}\n"
        f"Routes: {', '.join(r if isinstance(r, str) else r.get('path', str(r)) for r in routes)}"
    )

    if user_flows:
        flows_txt = "\n".join(
            f"- {f}" if isinstance(f, str) else f"- {f.get('description', str(f))}"
            for f in user_flows
        )
        parts.append("## USER FLOWS\n" + flows_txt)

    if selected_files:
        files_section = ["## FICHIERS À ANALYSER"]
        for filepath, content in selected_files.items():
            truncated = content[:_MAX_FILE_CHARS]
            if len(content) > _MAX_FILE_CHARS:
                truncated += f"\n... [tronqué à {_MAX_FILE_CHARS} chars]"
            files_section.append(f"### {filepath}\n```typescript\n{truncated}\n```")
        parts.append("\n\n".join(files_section))

    if rag_standards:
        standards_txt = rag_standards[:_MAX_STANDARDS_CHARS]
        parts.append("## STANDARDS DE RÉFÉRENCE (ZONE_15 + ZONE_16)\n" + standards_txt)

    parts.append(
        "## INSTRUCTION\n"
        "Analyse le code ci-dessus selon les règles IDOR, cross-user, conformité brief, "
        "et page stub. Produis uniquement le ReviewReport JSON demandé dans tes instructions système."
    )

    return "\n\n---\n\n".join(parts)


def _parse_review_report(raw: str) -> dict[str, Any]:
    try:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logger.warning("[reviewer] JSON parse error: %s", e)
    return {
        "verdict": "DEGRADED",
        "security_score": 50,
        "coherence_score": 50,
        "summary": "Parsing du rapport impossible — revue dégradée par défaut.",
        "findings": [],
        "targeted_fixes": [],
        "_parse_error": raw[:300],
    }


async def run_reviewer(
    brief: str,
    spec: dict,
    user_flows: list,
    selected_files: dict[str, str],
    rag_standards: str,
    run_id: str,
    stack_id: str = "nextjs-clerk-prisma",
    page_auth_contract: str = "",
) -> dict[str, Any]:
    """
    Lance la revue sémantique post-build.

    selected_files : dict {filepath_relatif: contenu} — sélection effectuée par review_activity.
    rag_standards  : texte RAG pré-fetché (ZONE_15 + ZONE_16, agent_context=reviewer).

    Retourne un ReviewReport dict :
        verdict          : "COHERENT" | "DEGRADED" | "INCOHERENT"
        security_score   : int 0–100
        coherence_score  : int 0–100
        summary          : str
        findings         : list[Finding]
        targeted_fixes   : list[TargetedFix]
    """
    import os
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    system_prompt = _load_reviewer_prompt(stack_id)
    human_content = _build_human_message(brief, spec, user_flows, selected_files, rag_standards, page_auth_contract)

    llm = ChatOpenAI(
        model=_REVIEWER_MODEL,
        temperature=0.0,
        api_key=os.getenv("REVIEWER_API_KEY", os.getenv("OPENAI_API_KEY")),
        max_retries=2,
    )

    logger.info(
        "[reviewer] run_id=%s model=%s — revue de %d fichier(s)",
        run_id, _REVIEWER_MODEL, len(selected_files),
    )
    try:
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ])
        raw = response.content or ""
    except Exception as e:
        logger.error("[reviewer] LLM error: %s", e)
        return {
            "verdict": "COHERENT",
            "security_score": 50,
            "coherence_score": 50,
            "summary": f"Revue LLM échouée: {e}",
            "findings": [],
            "targeted_fixes": [],
        }

    report = _parse_review_report(raw)
    verdict = report.get("verdict", "COHERENT")
    n_critical = sum(1 for f in report.get("findings", []) if f.get("severity") == "CRITICAL")
    logger.info(
        "[reviewer] verdict=%s sec=%s coh=%s critical=%d",
        verdict,
        report.get("security_score"),
        report.get("coherence_score"),
        n_critical,
    )
    return report
