# agents/dev_tools.py
"""
Outils Python natifs pour le dev agent v4 (Nouvelle Base).
Remplace le transport MCP (filesystem + shell MCP servers).
5 outils, zéro legacy, zéro dette.
28 Mars 2026.
"""
from __future__ import annotations

import os
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
