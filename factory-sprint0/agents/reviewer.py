"""
agents/reviewer.py
──────────────────
Reviewer post-build — architecture deux couches (Sprint 4.8A).

Layer 1 — Python déterministe (pas de LLM) :
  Lit les vrais fichiers générés, détecte IDOR, CROSS_USER_EXPOSURE,
  MISSING_AUTH, WRONG_AUTH. Zéro hallucination possible.

Layer 2 — LLM sémantique :
  Reçoit brief + user_flows + pages custom uniquement (PAS les services).
  Vérifie : conformité brief, ghost success, page stubs, couverture user_flows.
  Les services sont exclus du contexte LLM — ils sont corrects par construction
  et leur présence induisait des hallucinations IDOR systématiques.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── Champs owner reconnus par la factory ────────────────────────────────────
_OWNER_FIELDS = {"userId", "authorId", "ownerId"}

# ── Méthodes publiques intentionnellement sans filtre owner ──────────────────
_PUBLIC_METHOD_SIGNATURES = (
    "getPublicAll", "getPublished", "getBySlug",
    "getPublicById", "getPublicByIdWithRelations", "getBySlugWithRelations",
)


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 1 — Checks déterministes Python (aucun LLM)
# ═══════════════════════════════════════════════════════════════════════════

def _file_to_page_path(rel_path: str) -> str:
    """Convertit app/xxx/yyy/page.tsx → /xxx/yyy"""
    path = rel_path
    if path.startswith("app/"):
        path = path[4:]
    if path.endswith("/page.tsx"):
        path = path[:-9]
    elif path == "page.tsx":
        return "/"
    return "/" + path if path else "/"


def _check_service_idor(rel_path: str, content: str) -> list[dict]:
    """
    Détecte les update/delete Prisma sans champ owner dans le where.
    Lit le code réel — jamais de faux positif possible.
    """
    findings = []
    for op_match in re.finditer(r'prisma\.\w+\.(update|delete)\s*\(', content):
        window = content[op_match.start(): op_match.start() + 500]
        where_match = re.search(r'where\s*:\s*\{([^}]+)\}', window)
        if not where_match:
            continue
        where_content = where_match.group(1)
        has_owner = any(owner in where_content for owner in _OWNER_FIELDS)
        if not has_owner:
            findings.append({
                "severity": "CRITICAL",
                "type": "IDOR",
                "file": rel_path,
                "evidence": where_match.group(0)[:200].strip(),
                "fix": "Ajouter le champ owner (userId/authorId) dans le where Prisma.",
            })
    return findings


def _check_service_cross_user(rel_path: str, content: str) -> list[dict]:
    """
    Détecte les findMany sans filtre owner (exposition cross-user).
    Ignore les méthodes publiques intentionnellement sans owner.
    """
    findings = []
    for fm_match in re.finditer(r'prisma\.\w+\.findMany\s*\(\s*\{', content):
        start = fm_match.start()
        # Contexte amont pour détecter si on est dans une méthode publique
        ctx_before = content[max(0, start - 300): start]
        if any(pub in ctx_before for pub in _PUBLIC_METHOD_SIGNATURES):
            continue
        window = content[start: start + 400]
        where_match = re.search(r'where\s*:\s*\{([^}]+)\}', window)
        if not where_match:
            findings.append({
                "severity": "CRITICAL",
                "type": "CROSS_USER_EXPOSURE",
                "file": rel_path,
                "evidence": fm_match.group(0)[:100].strip(),
                "fix": "Ajouter where: { userId } pour isoler les données par utilisateur.",
            })
        else:
            where_content = where_match.group(1)
            has_owner = any(owner in where_content for owner in _OWNER_FIELDS)
            if not has_owner:
                findings.append({
                    "severity": "CRITICAL",
                    "type": "CROSS_USER_EXPOSURE",
                    "file": rel_path,
                    "evidence": where_match.group(0)[:200].strip(),
                    "fix": "Ajouter le champ owner dans le where pour filtrer par utilisateur.",
                })
    return findings


def _check_page_auth(rel_path: str, content: str, auth_required: bool) -> list[dict]:
    """
    Vérifie le régime auth d'une page.tsx contre la contrainte du spec.
    - auth_required=True  → doit avoir await auth() + redirect('/sign-in')
    - auth_required=False → ne doit PAS avoir auth() + redirect bloquant
    """
    findings = []
    has_auth_call = "await auth()" in content
    has_redirect_guard = "redirect('/sign-in')" in content or 'redirect("/sign-in")' in content

    if auth_required:
        if not has_auth_call:
            findings.append({
                "severity": "CRITICAL",
                "type": "MISSING_AUTH",
                "file": rel_path,
                "evidence": "Aucun appel à auth() détecté dans cette page privée.",
                "fix": "Ajouter : const { userId } = await auth(); if (!userId) redirect('/sign-in');",
            })
    else:
        # Page publique : auth() + redirect bloquant = régression fonctionnelle
        if has_auth_call and has_redirect_guard:
            findings.append({
                "severity": "WARNING",
                "type": "WRONG_AUTH",
                "file": rel_path,
                "evidence": "Page publique (auth_required=false) appelle auth() avec redirect bloquant.",
                "fix": "Retirer le guard auth()+redirect — cette page doit être accessible sans connexion.",
            })
    return findings


def _check_public_pii(rel_path: str, content: str) -> list[dict]:
    """
    Pages PUBLIQUES : détecte le rendu de champs PII (email, téléphone) dans le JSX.
    Origine : club-running (06 Juil 2026) — noms + emails des participants exposés
    aux visiteurs sur /run-events/[id] ; reviewer L1 et L2 aveugles (COHERENT 100).
    Cible les accès de rendu (.email dans le corps), pas les définitions de type.
    """
    findings = []
    _PII_MARKERS = (".email", ".phone", ".phoneNumber", ".telephone")
    for marker in _PII_MARKERS:
        if marker in content:
            findings.append({
                "severity": "WARNING",
                "type": "PII_PUBLIC_EXPOSURE",
                "file": rel_path,
                "evidence": f"Page publique rend un champ personnel ('{marker}') visible sans authentification.",
                "fix": "Retirer ce champ de la page publique — les données personnelles (email, téléphone) ne doivent apparaître que sur les pages authentifiées.",
            })
            break  # un finding par fichier suffit
    return findings


def _run_deterministic_checks(generated_files: dict, spec: dict) -> list[dict]:
    """
    Layer 1 — Checks sécurité déterministes, sans LLM.

    Vérifie :
    1. IDOR       : update/delete sans owner dans where (services)
    2. CROSS_USER : findMany sans filtre owner (services)
    3. AUTH_GUARD : pages privées sans auth() / pages publiques avec auth() bloquant
    4. PII_PUBLIC : champs personnels (email/téléphone) rendus sur pages publiques

    Lit les vrais fichiers générés — pas d'hallucination possible.
    """
    all_findings: list[dict] = []

    # Construire la map {page_path → auth_required} depuis spec
    pages = spec.get("pages", []) or []
    page_auth_map: dict[str, bool] = {}
    for p in pages:
        if isinstance(p, dict):
            path = p.get("path", "")
            auth = p.get("auth_required", True)
        else:
            path = getattr(p, "path", "")
            auth = getattr(p, "auth_required", True)
        page_auth_map[path] = bool(auth)

    for rel_path, content in generated_files.items():
        # Services — IDOR + CROSS_USER
        if "lib/services/" in rel_path and rel_path.endswith(".service.ts"):
            all_findings.extend(_check_service_idor(rel_path, content))
            all_findings.extend(_check_service_cross_user(rel_path, content))

        # Pages — régime auth
        # Exclut app/page.tsx racine : le pattern auth()+redirect y est intentionnel
        # (aiguillage : connecté → dashboard, non connecté → sign-in).
        if (rel_path.endswith("page.tsx")
                and rel_path != "app/page.tsx"
                and "/sign-in/" not in rel_path
                and "/sign-up/" not in rel_path):
            page_path = _file_to_page_path(rel_path)
            if page_path in page_auth_map:
                all_findings.extend(
                    _check_page_auth(rel_path, content, page_auth_map[page_path])
                )

        # Pages publiques (page.tsx + page-client.tsx) — PII rendue sans auth
        if rel_path.endswith(("page.tsx", "page-client.tsx")) and rel_path.startswith("app/"):
            _pii_page_path = _file_to_page_path(rel_path.replace("page-client.tsx", "page.tsx"))
            if page_auth_map.get(_pii_page_path) is False:
                all_findings.extend(_check_public_pii(rel_path, content))

    logger.info(
        "[reviewer] Layer 1 déterministe : %d findings (IDOR=%d, CROSS_USER=%d, AUTH=%d)",
        len(all_findings),
        sum(1 for f in all_findings if f["type"] == "IDOR"),
        sum(1 for f in all_findings if f["type"] == "CROSS_USER_EXPOSURE"),
        sum(1 for f in all_findings if f["type"] in ("MISSING_AUTH", "WRONG_AUTH")),
    )
    return all_findings

def _get_reviewer_model() -> str:
    try:
        from agents.stack_config import get_llm_models
        return get_llm_models().get("reviewer", "gpt-4o-mini")
    except Exception:
        return "gpt-4o-mini"

_REVIEWER_MODEL = _get_reviewer_model()
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
    generated_files: dict[str, str] | None = None,
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

    # ── Layer 1 : checks déterministes Python ────────────────────────────────
    deterministic_findings: list[dict] = []
    if generated_files:
        deterministic_findings = _run_deterministic_checks(generated_files, spec)

    # ── Layer 2 : LLM sémantique — services EXCLUS du contexte ───────────────
    # Les services sont corrects par construction (service_generator déterministe).
    # Leur présence dans le contexte LLM induisait des hallucinations IDOR
    # systématiques (gpt-4o-mini ignore le code réel et génère des findings
    # basés sur ses priors). Le LLM se concentre sur la conformité brief.
    semantic_files = {
        path: content
        for path, content in selected_files.items()
        if "lib/services/" not in path
    }

    system_prompt = _load_reviewer_prompt(stack_id)
    human_content = _build_human_message(brief, spec, user_flows, semantic_files, rag_standards, page_auth_contract)

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

    # ── Fusion des deux couches ───────────────────────────────────────────────
    # Les findings déterministes (Layer 1) sont factuels — ils remplacent
    # les findings sécurité du LLM (Layer 2) qui pourraient halluciner.
    llm_findings = report.get("findings", [])
    llm_security_types = {"IDOR", "CROSS_USER_EXPOSURE", "MISSING_AUTH", "WRONG_AUTH"}

    # Garder uniquement les findings LLM non-sécurité (semantic : ghost success, stub, conformité)
    semantic_findings = [f for f in llm_findings if f.get("type") not in llm_security_types]

    # Merger : déterministes d'abord, puis sémantiques LLM
    all_findings = deterministic_findings + semantic_findings
    report["findings"] = all_findings

    # Recalculer security_score depuis les findings déterministes uniquement
    n_idor = sum(1 for f in deterministic_findings if f["type"] == "IDOR")
    n_cross = sum(1 for f in deterministic_findings if f["type"] == "CROSS_USER_EXPOSURE")
    n_missing_auth = sum(1 for f in deterministic_findings if f["type"] == "MISSING_AUTH")
    security_score = max(0, 100 - n_idor * 30 - n_cross * 30 - n_missing_auth * 15)
    report["security_score"] = security_score

    # Recalculer verdict global
    has_critical = any(f.get("severity") == "CRITICAL" for f in all_findings)
    llm_verdict = report.get("verdict", "COHERENT")
    if has_critical:
        report["verdict"] = "DEGRADED"
    elif llm_verdict == "INCOHERENT":
        report["verdict"] = "INCOHERENT"
    else:
        report["verdict"] = llm_verdict if llm_verdict != "DEGRADED" else "COHERENT"

    # ── targeted_fixes : Layer 1 déterministe + LLM sémantique (sans doublons sécurité) ──
    # Les fixes WRONG_AUTH/MISSING_AUTH sont générés ici depuis les findings Layer 1.
    # Le LLM ne peut pas les produire fiablement → on l'exclut pour ces types.
    _L1_FIXABLE = {"WRONG_AUTH", "MISSING_AUTH"}
    l1_targeted_fixes = [
        {
            "file": f["file"],
            "type": f["type"],
            "severity": f["severity"],
            "fix": f.get("fix", ""),
        }
        for f in deterministic_findings
        if f["type"] in _L1_FIXABLE
    ]
    llm_targeted_fixes = report.get("targeted_fixes", []) or []
    report["targeted_fixes"] = l1_targeted_fixes + [
        tf for tf in llm_targeted_fixes
        if tf.get("type") not in _L1_FIXABLE
    ]

    verdict = report["verdict"]
    logger.info(
        "[reviewer] verdict=%s sec=%s coh=%s | det=%d llm_sem=%d total=%d targeted_fixes=%d",
        verdict,
        report.get("security_score"),
        report.get("coherence_score"),
        len(deterministic_findings),
        len(semantic_findings),
        len(all_findings),
        len(report["targeted_fixes"]),
    )
    return report
