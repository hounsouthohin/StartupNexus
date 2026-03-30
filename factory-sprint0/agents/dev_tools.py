# agents/dev_tools.py
"""
Outils Python natifs pour le dev agent v4 (Nouvelle Base).
Remplace le transport MCP (filesystem + shell MCP servers).
5 outils, zéro legacy, zéro dette.
28 Mars 2026.
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

from langchain_core.tools import tool

_BASE_WORKDIR = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")
_runtime_workdir: str | None = None
_protected_files: set[str] = set()


def _get_workdir() -> str:
    """Retourne le workdir actif pour ce run (projet-spécifique si set_workdir a été appelé)."""
    return _runtime_workdir or _BASE_WORKDIR


def set_workdir(path: str | None) -> None:
    """Fixe le workdir pour le run courant. Passer None pour réinitialiser."""
    global _runtime_workdir
    _runtime_workdir = path


def set_protected_files(paths: list[str] | set[str] | None) -> None:
    """
    Définit la liste des fichiers protégés contre réécriture pendant un run.
    Les chemins sont normalisés en style posix relatif au workdir.
    """
    global _protected_files
    if not paths:
        _protected_files = set()
        return
    normalized = {
        str(p).strip().replace("\\", "/").lstrip("/")
        for p in paths
        if str(p).strip()
    }
    _protected_files = normalized


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
    try:
        norm_path = str(path).strip().replace("\\", "/").lstrip("/")
        abs_path = _safe_path(path)
        if norm_path in _protected_files and os.path.exists(abs_path):
            return (
                f"ERREUR write_file({path}): fichier protégé par template. "
                "Lis-le avec read_file() et évite toute réécriture."
            )
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        Path(abs_path).write_text(content, encoding="utf-8")
        return f"OK: {path} écrit ({len(content)} chars)"
    except Exception as e:
        return f"ERREUR write_file({path}): {e}"


@tool
def read_file(path: str) -> str:
    """
    Lit un fichier depuis le répertoire de travail du projet.
    path: chemin relatif (ex: 'app/layout.tsx', 'package.json')
    """
    try:
        abs_path = _safe_path(path)
        if not os.path.exists(abs_path):
            return f"ABSENT: {path} n'existe pas"
        content = Path(abs_path).read_text(encoding="utf-8", errors="replace")
        if len(content) > 8000:
            return content[:8000] + f"\n... [tronqué — {len(content)} chars total]"
        return content
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
    if not _protected_files:
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

    for pf in _protected_files:
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
    # Ces commandes ne peuvent pas tourner dans un pipeline non-interactif.
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
    try:
        # shell=True intentionnel : le LLM a besoin de npm, tsc, prisma, etc.
        # Containment : cwd forcé sur le workdir projet + timeout 120s.
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=_get_workdir(),
        )
        output = (result.stdout + result.stderr).strip()
        status = "OK" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
        return f"{status}\n{output[:4000]}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT: commande dépassée 120s"
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
