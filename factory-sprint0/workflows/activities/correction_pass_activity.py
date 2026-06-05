"""
workflows/activities/correction_pass_activity.py
─────────────────────────────────────────────────
Temporal Activity — Correction chirurgicale post-review (Sprint 4.8A').

Deux niveaux de correction :
  Level 1 — Déterministe Python (sans LLM) :
    WRONG_AUTH sur page publique : supprime auth()+redirect si userId non utilisé en aval.
    MISSING_AUTH sur page privée  : ajoute le guard auth() manquant.

  Level 2 — LLM mini-correction (1 appel ciblé) :
    BRIEF_CONFORMITY sur page custom : re-génère la page avec le finding comme contrainte.

Ne touche JAMAIS les fichiers protégés (services, actions, types, schemas, middleware).
Rebuild : saute npm install (node_modules déjà présent), lance uniquement npm run build.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

from temporalio import activity
from temporalio.exceptions import ApplicationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

_SUBPROCESS_TIMEOUT = 300

# Fichiers jamais modifiés par correction_pass (indépendamment de la stack config)
_ALWAYS_PROTECTED = frozenset({
    "lib/prisma.ts", "lib/types.ts", "lib/schemas.ts",
    "prisma.config.ts", "prisma/schema.prisma",
    ".eslintrc.stack.json", "middleware.ts",
    "lib/logger.ts", "lib/prisma-errors.ts",
})

# Types de findings actionnables par correction_pass
_FIXABLE_TYPES = {"WRONG_AUTH", "MISSING_AUTH", "BRIEF_CONFORMITY"}


# ══════════════════════════════════════════════════════════════════════════
# Helpers : détection du scope
# ══════════════════════════════════════════════════════════════════════════

def _is_custom_page(rel_path: str) -> bool:
    """
    True si le fichier est une page custom LLM-générée (pas un fichier protégé).
    Seules ces pages peuvent être corrigées par correction_pass.
    """
    if not rel_path.endswith("page.tsx"):
        return False
    if rel_path in _ALWAYS_PROTECTED:
        return False
    # Exclure les pages déterministes protégées (sign-in, sign-up, etc.)
    protected_paths = ("sign-in", "sign-up")
    return not any(p in rel_path for p in protected_paths)


def _uses_userid_after_auth(content: str) -> bool:
    """
    True si userId est utilisé dans le corps de la fonction après le guard auth().
    Empêche de supprimer l'auth guard si userId est nécessaire pour des appels service.
    """
    # Retirer les lignes auth pour voir ce qui reste
    without_auth = re.sub(r'const \{ userId \} = await auth\(\).*', "", content)
    without_auth = re.sub(r"import \{ auth \} from.*", "", without_auth)
    return "userId" in without_auth


# ══════════════════════════════════════════════════════════════════════════
# Level 1 — Corrections déterministes Python
# ══════════════════════════════════════════════════════════════════════════

def _fix_wrong_auth_public_page(content: str) -> Tuple[str, bool]:
    """
    Supprime le guard auth()+redirect d'une page qui devrait être publique.
    Ne s'applique que si userId n'est pas utilisé en aval (safe).
    Retourne (nouveau_contenu, was_modified).
    """
    if not _uses_userid_after_auth(content):
        # Safe : userId n'est pas utilisé après l'auth guard
        new_content = content
        # Supprimer import auth
        new_content = re.sub(
            r"import\s*\{[^}]*\bauth\b[^}]*\}\s*from\s*['\"]@clerk/nextjs/server['\"];?\s*\n?",
            "", new_content
        )
        # Supprimer const { userId } = await auth()
        new_content = re.sub(r"\s*const\s*\{\s*userId\s*\}\s*=\s*await\s*auth\(\);?\s*\n?", "\n", new_content)
        # Supprimer if (!userId) redirect(...)
        new_content = re.sub(r"\s*if\s*\(!userId\)\s*redirect\(['\"][^'\"]*['\"]\);?\s*\n?", "\n", new_content)
        # Nettoyer les doubles lignes vides
        new_content = re.sub(r"\n{3,}", "\n\n", new_content).strip() + "\n"
        return new_content, new_content != content

    # userId utilisé en aval → correction LLM nécessaire
    return content, False


def _fix_missing_auth_private_page(content: str) -> Tuple[str, bool]:
    """
    Ajoute le guard auth()+redirect à une page privée qui n'en a pas.
    """
    if "await auth()" in content:
        return content, False  # déjà présent

    # Ajouter l'import auth si absent
    has_clerk_import = "@clerk/nextjs/server" in content
    has_redirect_import = "next/navigation" in content and "redirect" in content

    lines = content.split("\n")
    new_lines = []
    injected = False

    for i, line in enumerate(lines):
        new_lines.append(line)
        # Injecter le guard après la déclaration de la fonction async
        if not injected and "async function" in line and "{" in line:
            if not has_clerk_import:
                # Ajouter les imports en haut
                new_lines = [
                    "import { auth } from '@clerk/nextjs/server'",
                    "import { redirect } from 'next/navigation'"
                    if not has_redirect_import else "",
                ] + new_lines
            new_lines.append("  const { userId } = await auth()")
            new_lines.append("  if (!userId) redirect('/sign-in')")
            injected = True

    if not injected:
        return content, False

    result = "\n".join(l for l in new_lines if l is not None)
    return result, True


# ══════════════════════════════════════════════════════════════════════════
# Level 2 — LLM mini-correction ciblée
# ══════════════════════════════════════════════════════════════════════════

async def _fix_brief_conformity_llm(
    rel_path: str,
    content: str,
    finding: Dict[str, Any],
    brief: str,
    spec: Dict[str, Any],
) -> Tuple[str, bool]:
    """
    Re-génère une page avec le finding comme contrainte ciblée.
    Appel LLM minimal : system prompt court + contenu actuel + finding + consigne précise.
    """
    try:
        import os
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        model = os.getenv("REVIEWER_API_KEY") and "gpt-4o" or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(
            model=model,
            temperature=0,
            api_key=os.getenv("REVIEWER_API_KEY", os.getenv("OPENAI_API_KEY")),
            max_retries=1,
        )

        system = (
            "Tu es un correcteur de code Next.js 15. "
            "Tu reçois un fichier page.tsx avec un problème détecté. "
            "Réécris le fichier pour corriger UNIQUEMENT le problème signalé. "
            "Conserve la structure et les imports valides. "
            "Réponds UNIQUEMENT avec le code corrigé — aucun texte, aucune explication."
        )

        evidence = finding.get("evidence", "")
        fix_hint = finding.get("fix", "")
        human = (
            f"BRIEF : {brief[:400]}\n\n"
            f"FICHIER : {rel_path}\n"
            f"```typescript\n{content[:3000]}\n```\n\n"
            f"PROBLÈME DÉTECTÉ : {evidence}\n"
            f"CORRECTION ATTENDUE : {fix_hint}\n\n"
            "Réécris ce fichier en corrigeant ce problème."
        )

        response = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        raw = response.content or ""
        # Extraire le code TypeScript
        code_match = re.search(r"```(?:typescript|tsx)?\s*([\s\S]+?)\s*```", raw)
        new_content = code_match.group(1) if code_match else raw.strip()
        if new_content and new_content != content:
            return new_content + "\n", True
    except Exception as e:
        activity.logger.warning(f"[correction_pass] LLM mini-correction échouée ({rel_path}): {e}")

    return content, False


# ══════════════════════════════════════════════════════════════════════════
# Orchestration des fixes
# ══════════════════════════════════════════════════════════════════════════

async def _process_finding(
    finding: Dict[str, Any],
    project_workdir: str,
    brief: str,
    spec: Dict[str, Any],
    protected_paths: frozenset,
) -> Optional[str]:
    """
    Tente de corriger un finding. Retourne le chemin du fichier modifié ou None.
    """
    rel_path = finding.get("file", "").strip()
    finding_type = finding.get("type", "")
    severity = finding.get("severity", "")

    if not rel_path or not _is_custom_page(rel_path):
        return None
    if rel_path in protected_paths:
        return None
    if finding_type not in _FIXABLE_TYPES:
        return None

    abs_path = pathlib.Path(project_workdir) / rel_path
    if not abs_path.exists():
        activity.logger.warning(f"[correction_pass] Fichier introuvable : {rel_path}")
        return None

    try:
        content = abs_path.read_text(encoding="utf-8")
    except Exception as e:
        activity.logger.warning(f"[correction_pass] Lecture impossible {rel_path}: {e}")
        return None

    new_content = content
    modified = False

    if finding_type == "WRONG_AUTH":
        new_content, modified = _fix_wrong_auth_public_page(content)
        if not modified:
            # userId utilisé en aval → escalade au LLM
            activity.logger.info(f"[correction_pass] WRONG_AUTH escaladé au LLM (userId en aval) : {rel_path}")
            new_content, modified = await _fix_brief_conformity_llm(rel_path, content, finding, brief, spec)

    elif finding_type == "MISSING_AUTH":
        new_content, modified = _fix_missing_auth_private_page(content)

    elif finding_type == "BRIEF_CONFORMITY":
        new_content, modified = await _fix_brief_conformity_llm(rel_path, content, finding, brief, spec)

    if modified and new_content:
        try:
            abs_path.write_text(new_content, encoding="utf-8")
            activity.logger.info(
                f"[correction_pass] ✓ {rel_path} corrigé ({finding_type} {severity})"
            )
            return rel_path
        except Exception as e:
            activity.logger.error(f"[correction_pass] Écriture échouée {rel_path}: {e}")

    return None


# ══════════════════════════════════════════════════════════════════════════
# Re-build (sans npm install — node_modules déjà présent)
# ══════════════════════════════════════════════════════════════════════════

def _rebuild_only(project_workdir: str) -> str:
    """
    Relance UNIQUEMENT npm run build (skip npm install).
    node_modules est déjà présent depuis le dev_test pass.
    Évite le problème dotenv de prisma.config.ts lors du postinstall.
    """
    package_json = os.path.join(project_workdir, "package.json")
    if not os.path.isfile(package_json):
        return "BUILD_FAILED: package.json introuvable"

    env = os.environ.copy()
    env["NODE_ENV"] = "production"
    env["NEXT_TELEMETRY_DISABLED"] = "1"

    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=project_workdir,
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
            env=env,
        )
        if result.returncode != 0:
            stderr = (result.stdout + result.stderr).strip()
            return f"BUILD_FAILED: {stderr[:2000]}"
        return "BUILD_SUCCESS"
    except subprocess.TimeoutExpired:
        return f"BUILD_FAILED: timeout ({_SUBPROCESS_TIMEOUT}s)"
    except Exception as e:
        return f"BUILD_FAILED: exception — {e}"


def _scan_workdir(project_workdir: str) -> Dict[str, str]:
    files: Dict[str, str] = {}
    EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".json", ".prisma", ".css", ".md"}
    NAMED_FILES = {".env.local", ".env", ".gitignore"}
    IGNORE_DIRS = {"node_modules", ".next", ".git", "dist", "build", ".turbo"}
    base = pathlib.Path(project_workdir)
    for root, dirs, filenames in os.walk(base):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext in EXTENSIONS or filename in NAMED_FILES:
                abs_path = pathlib.Path(root) / filename
                rel = abs_path.relative_to(base).as_posix()
                try:
                    files[rel] = abs_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass
    return files


# ══════════════════════════════════════════════════════════════════════════
# Temporal Activity
# ══════════════════════════════════════════════════════════════════════════

@activity.defn(name="correction_pass_activity")
async def correction_pass_activity(
    input_data: Dict[str, Any],
    run_id: str = "",
) -> Dict[str, Any]:
    """
    Correction chirurgicale post-review (Sprint 4.8A').

    Input attendu :
        project_name    : str
        stack_id        : str
        findings        : list[dict]  — depuis ReviewReport (nouveaux)
        targeted_fixes  : list[dict]  — backward compat (ignoré si findings présents)
        review_verdict  : str
        brief           : str
        spec            : dict

    Output :
        correction_applied  : bool
        files_modified      : list[str]
        new_build_status    : str
        updated_files       : dict[str, str]
    """
    project_name = input_data.get("project_name", "projet-sans-nom")
    stack_id = str(input_data.get("stack_id", "nextjs-clerk-prisma"))
    findings: List[Dict] = input_data.get("findings", []) or []
    review_verdict = str(input_data.get("review_verdict", "COHERENT"))
    brief = str(input_data.get("brief", ""))
    spec = input_data.get("spec", {}) or {}

    factory_workdir = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")
    project_workdir = os.path.join(factory_workdir, project_name)

    # Filtrer les findings actionnables (CRITICAL ou WARNING sur pages custom)
    actionable = [
        f for f in findings
        if f.get("type") in _FIXABLE_TYPES
        and f.get("severity") in ("CRITICAL", "WARNING")
        and _is_custom_page(f.get("file", ""))
    ]

    activity.logger.info(
        f"[correction_pass] Démarrage — projet={project_name} "
        f"verdict={review_verdict} findings={len(findings)} actionnables={len(actionable)}"
    )

    if not actionable:
        activity.logger.info("[correction_pass] Aucun finding actionnable — skip")
        return {
            "correction_applied": False,
            "files_modified": [],
            "new_build_status": "BUILD_SUCCESS",
            "updated_files": {},
        }

    if not os.path.isdir(project_workdir):
        raise ApplicationError(
            "CORRECTION_WORKDIR_MISSING",
            f"Project workdir introuvable: {project_workdir}",
        )

    # Charger les fichiers protégés depuis la stack config
    _protected_paths = frozenset(_ALWAYS_PROTECTED)
    try:
        from agents.stack_config import load_stack_config
        _cfg = load_stack_config(stack_id)
        _protected_paths = frozenset(_cfg.get("protected_files", [])) | _protected_paths
    except Exception as _pe:
        activity.logger.warning("[correction_pass] stack_config non disponible: %s", _pe)

    # Appliquer les corrections (max 3 findings)
    files_modified: List[str] = []
    for finding in actionable[:3]:
        modified_path = await _process_finding(
            finding, project_workdir, brief, spec, _protected_paths
        )
        if modified_path:
            files_modified.append(modified_path)

    if not files_modified:
        activity.logger.info("[correction_pass] Aucun fichier modifié après traitement des findings")
        return {
            "correction_applied": False,
            "files_modified": [],
            "new_build_status": "BUILD_SUCCESS",
            "updated_files": {},
        }

    # Re-build (sans npm install — évite le problème dotenv)
    new_build_status = _rebuild_only(project_workdir)
    activity.logger.info(f"[correction_pass] Re-build → {new_build_status[:80]}")

    updated_files = _scan_workdir(project_workdir) if new_build_status == "BUILD_SUCCESS" else {}

    return {
        "correction_applied": True,
        "files_modified": files_modified,
        "new_build_status": new_build_status,
        "updated_files": updated_files,
    }
