"""
agents/reviewer.py
──────────────────
Reviewer post-build — contrôles déterministes (Layer 1) uniquement.

Lit les vrais fichiers générés : pages privées sans auth(), pages publiques avec auth()
bloquant, données personnelles rendues sur des pages publiques. Zéro hallucination possible.

La couche LLM (Layer 2, gpt-4o : « conformité brief ») a été retirée le 30 sept 2026 :
elle notait COHERENT 100/100 des apps absurdes. Le jugement du comportement viendra des
oracles dérivés de la déclaration (USINE.md §5).
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


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


# NOTE (9 Juil 2026) : _check_service_idor / _check_service_cross_user SUPPRIMÉS.
# Raison : les services sont 100% déterministes (service_modules/), protégés (le LLM ne les
# écrit jamais) et verrouillés par tests de générateur — leur ownership est garanti à la SOURCE.
# Les regex à where-plat produisaient des faux positifs (accolades imbriquées du fix M2M) sur du
# code sûr. Cf. mémoire feedback_no_regex + project_guards_map (guard symptomatique retiré).


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
    # Accès de rendu à un champ PII : .email, .contactEmail, .phone, .mobilePhone,
    # .telephone, .tel… — insensible à la casse, quel que soit le préfixe camelCase.
    _m = re.search(r"\.\w*(?:[Ee]mail|[Pp]hone|[Tt]elephone|[Mm]obile)\b", content)
    if _m:
        findings.append({
            "severity": "WARNING",
            "type": "PII_PUBLIC_EXPOSURE",
            "file": rel_path,
            "evidence": f"Page publique rend un champ personnel ('{_m.group(0)}') sans authentification.",
            "fix": "Retirer ce champ de la page publique — les données personnelles (email, téléphone) ne doivent apparaître que sur les pages authentifiées.",
        })
    return findings


def _run_deterministic_checks(generated_files: dict, spec: dict) -> list[dict]:
    """
    Layer 1 — Checks déterministes portant UNIQUEMENT sur le code écrit par le LLM (pages).

    Vérifie :
    1. AUTH_GUARD : pages privées sans auth() / pages publiques avec auth() bloquant
    2. PII_PUBLIC : champs personnels (email/téléphone) rendus sur pages publiques

    Les services (lib/services/*) sont 100% DÉTERMINISTES, protégés (le LLM ne les écrit jamais)
    et verrouillés par des tests de générateur : leur ownership est GARANTI à la source (crud.py).
    Y appliquer des checks regex ne pouvait que produire des faux positifs — le fix ownership M2M
    `where: { id: { in: tagIds }, userId }` (accolades imbriquées) cassait la regex à plat et faisait
    crier CROSS_USER sur du code SÛR (9 Juil). Les checks IDOR/CROSS_USER regex sur services sont donc
    RETIRÉS (cf. mémoire feedback_no_regex + leçon DY6 : ne pas re-vérifier du déterministe protégé).

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
        # Pages — régime auth (code LLM : garde légitime)
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

        # Pages publiques (page.tsx + page-client.tsx) — PII rendue sans auth (code LLM)
        if rel_path.endswith(("page.tsx", "page-client.tsx")) and rel_path.startswith("app/"):
            _pii_page_path = _file_to_page_path(rel_path.replace("page-client.tsx", "page.tsx"))
            if page_auth_map.get(_pii_page_path) is False:
                all_findings.extend(_check_public_pii(rel_path, content))

    logger.info(
        "[reviewer] Layer 1 déterministe (pages LLM) : %d findings (AUTH=%d, PII=%d)",
        len(all_findings),
        sum(1 for f in all_findings if f["type"] in ("MISSING_AUTH", "WRONG_AUTH")),
        sum(1 for f in all_findings if f["type"] == "PII_PUBLIC_EXPOSURE"),
    )
    return all_findings


# ═══════════════════════════════════════════════════════════════════════════
# Point d'entrée
# ═══════════════════════════════════════════════════════════════════════════

# Types de findings que correction_pass sait corriger de façon déterministe.
_L1_FIXABLE = {"WRONG_AUTH", "MISSING_AUTH"}


def run_reviewer(spec: dict, generated_files: dict[str, str] | None, run_id: str = "") -> dict[str, Any]:
    """
    Revue post-build — contrôles déterministes uniquement.

    Retourne un ReviewReport dict :
        verdict          : "DEGRADED" si un finding CRITICAL, sinon "COHERENT"
        security_score   : int 0–100 (dérivé des findings auth / PII)
        summary          : str
        findings         : list[Finding]
        targeted_fixes   : list[TargetedFix] (findings corrigeables par correction_pass)
    """
    findings = _run_deterministic_checks(generated_files or {}, spec)

    n_missing_auth = sum(1 for f in findings if f["type"] == "MISSING_AUTH")
    n_pii = sum(1 for f in findings if f["type"] == "PII_PUBLIC_EXPOSURE")
    verdict = "DEGRADED" if any(f.get("severity") == "CRITICAL" for f in findings) else "COHERENT"
    report = {
        "verdict": verdict,
        "security_score": max(0, 100 - n_missing_auth * 30 - n_pii * 15),
        "summary": (
            f"{len(findings)} problème(s) détecté(s) par les contrôles déterministes "
            "(authentification des pages, données personnelles sur les pages publiques)."
        ),
        "findings": findings,
        "targeted_fixes": [
            {"file": f["file"], "type": f["type"], "severity": f["severity"], "fix": f.get("fix", "")}
            for f in findings
            if f["type"] in _L1_FIXABLE
        ],
    }
    logger.info(
        "[reviewer] run_id=%s verdict=%s sec=%s findings=%d",
        run_id, verdict, report["security_score"], len(findings),
    )
    return report

