# agents/dev_tools.py
"""
Outils Python natifs pour le dev agent v4 (Nouvelle Base).
Remplace le transport MCP (filesystem + shell MCP servers).
5 outils, zéro legacy, zéro dette.
28 Mars 2026.

R5-v2 (24 Avril 2026) — Isolation par contexte asyncio (ContextVar) :
  dev_test_activity est async — elle await LangGraph dont le ToolNode invoque
  les outils synchrones via asyncio.run_in_executor(). CPython propage le
  contexte ContextVar aux threads executor via contextvars.copy_context().
  threading.local() n'est PAS propagé par run_in_executor → workdir invisible
  dans les threads outils → ENOENT (R5-v1 bug, corrigé ici).

  Isolation entre runs concurrents : chaque activité Temporal async tourne dans
  sa propre asyncio.Task — les ContextVar sont isolés par Task par défaut.
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
from contextvars import ContextVar
from pathlib import Path

from langchain_core.tools import tool

_BASE_WORKDIR = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")

# ── ContextVar state — propagé par asyncio.run_in_executor aux threads outils ─
_workdir_cv:   ContextVar[str | None]        = ContextVar("factory_workdir",   default=None)
_protected_cv: ContextVar[frozenset[str]]    = ContextVar("factory_protected",  default=frozenset())
_forbidden_cv: ContextVar[frozenset[str]]    = ContextVar("factory_forbidden",  default=frozenset())


# ── Accesseurs internes ───────────────────────────────────────────────────────

def _get_workdir() -> str:
    return _workdir_cv.get() or _BASE_WORKDIR


def _get_protected_files() -> frozenset[str]:
    return _protected_cv.get()


# ── API publique de gestion d'état ────────────────────────────────────────────

def set_workdir(path: str | None) -> None:
    """Fixe le workdir pour le run courant. Passer None pour réinitialiser."""
    _workdir_cv.set(path)


def set_protected_files(paths: list[str] | set[str] | None) -> None:
    """
    Définit la liste des fichiers protégés contre réécriture pendant un run.
    Les chemins sont normalisés en style posix relatif au workdir.
    """
    if not paths:
        _protected_cv.set(frozenset())
        return
    _protected_cv.set(frozenset(
        str(p).strip().replace("\\", "/").lstrip("/")
        for p in paths
        if str(p).strip()
    ))


def set_forbidden_imports(tokens: list[str]) -> None:
    """Charge les tokens d'import interdits depuis la stack config (forbidden_imports[])."""
    _forbidden_cv.set(frozenset(t.lower() for t in tokens if t))


def _safe_path(path: str) -> str:
    """Résout un chemin relatif dans le workdir actif. Refuse les path traversal."""
    base = Path(_get_workdir()).resolve()
    clean = path.lstrip("/")
    target = (base / clean).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError(f"Path traversal refusé : {path}")
    return str(target)


@tool
def write_file(path: str, content: str) -> str:
    """
    Écrit (ou écrase) un fichier dans le répertoire de travail du projet.
    path: chemin relatif (ex: 'app/layout.tsx', 'package.json', '.env.local')
    content: contenu complet du fichier
    """
    import json as _json
    try:
        norm_path = str(path).strip().replace("\\", "/").lstrip("/")
        abs_path = _safe_path(path)

        # Guard 1 : fichiers protégés par template (écrits par la factory avant le LLM).
        # Pas de vérification os.path.exists — un fichier protégé reste protégé même si
        # supprimé via shell_exec. La restauration est assurée par restore_protected_node.
        if norm_path in _get_protected_files():
            return (
                f"ERREUR write_file({path}): fichier protégé par template. "
                "Lis-le avec read_file() et évite toute réécriture."
            )

        # Guard 2 : imports interdits par la stack config (forbidden_imports[]).
        # Vérifié uniquement dans les fichiers .ts/.tsx, sur les lignes d'import.
        if norm_path.endswith((".ts", ".tsx")):
            _forbidden = _forbidden_cv.get()
            if _forbidden:
                _import_lines = [
                    ln for ln in (content or "").splitlines()
                    if ln.lstrip().startswith("import ")
                ]
                for _il in _import_lines:
                    _il_lower = _il.lower()
                    for _tok in _forbidden:
                        if _tok in _il_lower:
                            return (
                                f"ERREUR write_file({path}): import interdit détecté — '{_tok}'.\n"
                                f"Ligne : {_il.strip()}\n"
                                "Supprime cet import et utilise l'alternative stack (Clerk, Prisma, Zod)."
                            )

        # Validation package.json : JSON strict requis.
        if norm_path == "package.json":
            try:
                parsed = _json.loads(content)
            except _json.JSONDecodeError as je:
                return (
                    f"ERREUR: package.json invalide (JSON parse failed). "
                    f"Ligne {je.lineno}, col {je.colno}: {je.msg}. "
                    "Réécris package.json avec un JSON strict (pas de virgule finale)."
                )
            if not isinstance(parsed, dict):
                return "ERREUR: package.json invalide (la racine doit être un objet JSON)."
            content = _json.dumps(parsed, ensure_ascii=False, indent=2) + "\n"

        # Validation prisma/schema.prisma : au moins un bloc model requis.
        if norm_path == "prisma/schema.prisma":
            if not re.search(r"(?m)^\s*model\s+\w+\s*\{", content or ""):
                return (
                    "ERREUR: prisma/schema.prisma incomplet — aucun bloc 'model Nom { ... }' trouvé. "
                    "Ajoute les modèles du brief avant d'écrire ce fichier."
                )

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        Path(abs_path).write_text(content, encoding="utf-8")
        return f"OK: {path} écrit ({len(content)} chars)"
    except Exception as e:
        return f"ERREUR write_file({path}): {e}"


@tool
def read_file(path: str, start_line: int = 0, end_line: int = 0) -> str:
    """
    Lit un fichier depuis le répertoire de travail du projet.
    path: chemin relatif (ex: 'app/layout.tsx', 'package.json')
    start_line: première ligne à lire, 1-indexé (obligatoire si fichier > 50 lignes)
    end_line: dernière ligne à lire incluse

    Workflow obligatoire pour un fichier inconnu :
      1. Appelle read_file("app/page.tsx") → reçois les métadonnées + aperçu 30 lignes
      2. Choisis ta plage selon le total de lignes indiqué
      3. Appelle read_file("app/page.tsx", 80, 120) → lis la section exacte

    Exemples :
      read_file("app/page.tsx")            → métadonnées + lignes 1-30
      read_file("app/page.tsx", 1, 50)     → lignes 1 à 50
      read_file("app/page.tsx", 80, 120)   → lignes 80 à 120 (autour d'une erreur ligne 87)
      read_file("package.json", 1, 30)     → package.json complet si < 30 lignes
    """
    try:
        abs_path = _safe_path(path)
        if not os.path.exists(abs_path):
            return f"ABSENT: {path} n'existe pas"
        content = Path(abs_path).read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        # ── Lecture par plage explicite ──────────────────────────────
        if start_line > 0 or end_line > 0:
            s = max(0, start_line - 1)
            e = end_line if end_line > 0 else total_lines
            e = min(e, total_lines)
            excerpt = "".join(lines[s:e])
            header = f"[{path} — lignes {s+1}-{e} sur {total_lines}]\n"
            return header + excerpt

        # ── Sans plage : métadonnées + aperçu des 30 premières lignes ─
        preview_end = min(30, total_lines)
        preview = "".join(lines[:preview_end])
        meta = f"[{path} — {total_lines} lignes au total]\n"
        if total_lines <= 30:
            return meta + content
        return (
            meta
            + preview
            + f"\n... [{total_lines - preview_end} lignes restantes]"
            + f"\n→ Pour lire la suite : read_file(\"{path}\", 31, 80)"
            + f"\n→ Pour aller à une erreur ligne N : read_file(\"{path}\", N-5, N+20)"
        )
    except Exception as e:
        return f"ERREUR read_file({path}): {e}"


@tool
def list_directory(path: str = ".") -> str:
    """
    Liste les fichiers et sous-dossiers d'un répertoire du projet.
    path: chemin relatif (défaut: racine du projet)
    """
    try:
        abs_path = _safe_path(path)
        if not os.path.exists(abs_path):
            return f"ABSENT: {path} n'existe pas"
        entries = []
        for entry in sorted(os.scandir(abs_path), key=lambda e: (not e.is_dir(), e.name)):
            prefix = "[DIR]  " if entry.is_dir() else "[FILE] "
            entries.append(f"{prefix}{entry.name}")
        return "\n".join(entries) if entries else "(dossier vide)"
    except Exception as e:
        return f"ERREUR list_directory({path}): {e}"


def _shell_exec_targets_protected(command: str) -> str | None:
    """
    Détecte si une commande shell tente d'écrire dans un fichier protégé.
    Retourne le nom du fichier concerné si détecté, None sinon.
    Patterns couverts : redirection (> / >> avec ou sans espace), tee, cp, mv.
    """
    protected = _get_protected_files()
    if not protected:
        return None
    cmd_lower = command.lower()

    def _norm_path_token(token: str) -> str:
        token = str(token or "").strip().strip("\"'").replace("\\", "/")
        while token.startswith("./"):
            token = token[2:]
        if token.startswith("/"):
            token = token[1:]
        return token

    def _targets_protected(token: str, protected_file: str) -> bool:
        t = _norm_path_token(token)
        pf = _norm_path_token(protected_file.lower())
        return bool(t) and (t == pf or t.endswith("/" + pf))

    for pf in protected:
        pf_lower = pf.lower()

        # Redirections shell: > file, >> file, >file, > "./file", etc.
        for m in re.finditer(r">{1,2}\s*([^\s;&|]+)", cmd_lower):
            if _targets_protected(m.group(1), pf_lower):
                return pf

        # tee file
        for m in re.finditer(r"\btee\b\s+([^\s;&|]+)", cmd_lower):
            if _targets_protected(m.group(1), pf_lower):
                return pf

        # cp src dest / mv src dest (dest = dernier argument)
        try:
            parts = shlex.split(cmd_lower, posix=True)
        except Exception:
            parts = cmd_lower.split()
        if parts and parts[0] in {"cp", "mv"} and len(parts) >= 3:
            if _targets_protected(parts[-1], pf_lower):
                return pf
    return None


@tool
def shell_exec(command: str) -> str:
    """
    Exécute une commande shell dans /app/generated-projects.
    Retourne stdout + stderr combinés (max 4000 chars).
    Préfixe 'OK' si exit code = 0, 'FAILED (exit N)' sinon.
    Exemples:
      shell_exec("npm install")
      shell_exec("tsc --noEmit")
      shell_exec("npm run build")
      shell_exec("npx prisma generate")
    """
    protected_target = _shell_exec_targets_protected(command)
    if protected_target:
        return (
            f"ERREUR shell_exec: fichier protégé '{protected_target}' — "
            "les fichiers template ne peuvent pas être réécrits via shell. "
            "Utilise write_file() si une modification contrôlée est requise."
        )

    # Guard anti-interactif : commandes qui bloquent en attendant une entrée utilisateur.
    _INTERACTIVE_BLOCKLIST = (
        "create-config",   # npx create-config / @eslint/create-config
        "eslint --init",   # ancienne commande d'init ESLint interactive
        "eslint-init",
        "npm init",        # npm init sans -y
        "npx init",
        "prisma init",     # interactive si déjà configuré
        "next telemetry",  # interactive
    )
    cmd_lower = command.strip().lower()
    for blocked in _INTERACTIVE_BLOCKLIST:
        if blocked in cmd_lower:
            return (
                f"ERREUR shell_exec: commande interactive bloquée ('{blocked}'). "
                "Cette commande attend une entrée utilisateur et ne peut pas tourner dans le pipeline. "
                "ESLint est déjà configuré via .eslintrc.stack.json — n'exécute pas de commande d'initialisation ESLint."
            )

    # Timeout adapté au type de commande.
    _COMMAND_TIMEOUTS: list[tuple[tuple[str, ...], int]] = [
        (("npm run build", "next build"),              300),
        (("npm install", "npm ci"),                    300),
        (("npx prisma generate", "prisma generate"),   120),
        (("npx prisma migrate", "prisma migrate"),     120),
        (("npx tsc", "tsc --"),                        120),
        (("npx eslint", "eslint "),                     60),
        (("npx jest", "jest "),                         90),
    ]
    timeout_s = 120  # défaut
    for patterns, t in _COMMAND_TIMEOUTS:
        if any(p in cmd_lower for p in patterns):
            timeout_s = t
            break

    # Environnement non-interactif : CI=true désactive les prompts et spinners.
    env = os.environ.copy()
    env["CI"] = "true"
    env["DEBIAN_FRONTEND"] = "noninteractive"
    env["NPM_CONFIG_YES"] = "true"
    env["NEXT_TELEMETRY_DISABLED"] = "1"

    try:
        # shell=True intentionnel : le LLM a besoin de npm, tsc, prisma, etc.
        # Containment : cwd forcé sur le workdir projet (thread-local).
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=_get_workdir(),
            env=env,
        )
        output = (result.stdout + result.stderr).strip()
        status = "OK" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
        return f"{status}\n{output[:4000]}"
    except subprocess.TimeoutExpired:
        return f"TIMEOUT: commande dépassée {timeout_s}s — '{command[:60]}'"
    except Exception as exc:
        return f"ERREUR shell_exec: {exc}"


@tool
def file_exists(path: str) -> str:
    """
    Vérifie si un fichier ou dossier existe dans le projet.
    path: chemin relatif (ex: 'package.json', 'app/layout.tsx')
    Retourne 'EXISTS' ou 'ABSENT'.
    """
    try:
        abs_path = _safe_path(path)
        return "EXISTS" if os.path.exists(abs_path) else "ABSENT"
    except Exception as e:
        return f"ERREUR file_exists({path}): {e}"
