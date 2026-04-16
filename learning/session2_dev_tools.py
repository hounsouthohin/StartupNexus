"""
SESSION 2 — Les outils du dev agent (dev_tools.py)
====================================================
Objectif : voir exactement ce que le LLM peut faire et ce qu'il reçoit
           en retour quand il appelle chaque outil.

Lance depuis la racine du projet :
    python learning/session2_dev_tools.py

Un dossier sandbox temporaire est créé dans learning/sandbox/
Il est supprimé automatiquement à la fin (sauf si --keep).
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

# ── Ajouter factory-sprint0 au path Python ───────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "factory-sprint0"))

import agents.dev_tools as dt

# ── Helpers d'affichage ──────────────────────────────────────────────────────

def sep(title=""):
    line = "─" * 60
    if title:
        print(f"\n┌{line}┐")
        print(f"│  {title:<58}│")
        print(f"└{line}┘")
    else:
        print(f"  {'─'*56}")

def show(label: str, result: str):
    print(f"\n  ▶ {label}")
    for line in result.split("\n"):
        print(f"      {line}")

def note(text: str):
    print(f"\n  💡 {text}")


# ── Setup sandbox ────────────────────────────────────────────────────────────

SANDBOX = Path(__file__).resolve().parent / "sandbox"

def setup_sandbox():
    SANDBOX.mkdir(parents=True, exist_ok=True)
    # Pointer les outils vers le sandbox
    dt.set_workdir(str(SANDBOX))
    dt.set_protected_files(None)
    print(f"\n  Sandbox créé : {SANDBOX}")


def teardown_sandbox():
    dt.set_workdir(None)
    dt.set_protected_files(None)
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
        print(f"\n  Sandbox supprimé.")


# ════════════════════════════════════════════════════════════════════════════
# OUTIL 1 — write_file
# ════════════════════════════════════════════════════════════════════════════

def test_write_file():
    sep("OUTIL 1 : write_file(path, content)")
    note("Le LLM appelle write_file pour créer ou écraser un fichier.")
    note("Il ne voit que la chaîne de retour — pas de confirmation visuelle.")

    # Cas 1 : écriture normale
    result = dt.write_file.invoke({"path": "app/page.tsx", "content": "export default function Home() {\n  return <h1>Hello</h1>\n}\n"})
    show("Écriture normale → app/page.tsx", result)

    # Cas 2 : sous-dossier créé automatiquement
    result = dt.write_file.invoke({"path": "app/api/users/route.ts", "content": "export async function GET() {\n  return Response.json({ users: [] })\n}\n"})
    show("Sous-dossier créé automatiquement → app/api/users/route.ts", result)

    # Cas 3 : réécriture d'un fichier existant
    result = dt.write_file.invoke({"path": "app/page.tsx", "content": "// version 2\nexport default function Home() {\n  return <h1>v2</h1>\n}\n"})
    show("Réécriture d'un fichier existant", result)

    # Cas 4 : fichier protégé (template)
    dt.set_protected_files(["app/layout.tsx"])
    # D'abord créer le fichier pour qu'il "existe"
    (SANDBOX / "app" / "layout.tsx").write_text("<!-- template -->", encoding="utf-8")
    result = dt.write_file.invoke({"path": "app/layout.tsx", "content": "tentative LLM"})
    show("Fichier protégé (template) — que voit le LLM ?", result)
    dt.set_protected_files(None)

    # Cas 5 : path traversal (attaque)
    result = dt.write_file.invoke({"path": "../../etc/passwd", "content": "hack"})
    show("Tentative de path traversal — protection activée ?", result)

    note("QUESTIONS : que se passe-t-il si write_file retourne ERREUR ?")
    note("           Le LLM lit le message d'erreur et essaie de corriger.")


# ════════════════════════════════════════════════════════════════════════════
# OUTIL 2 — read_file
# ════════════════════════════════════════════════════════════════════════════

def test_read_file():
    sep("OUTIL 2 : read_file(path)")
    note("Le LLM lit un fichier pour voir son contenu actuel avant de le modifier.")

    # Cas 1 : lecture normale
    result = dt.read_file.invoke({"path": "app/page.tsx"})
    show("Lecture d'un fichier existant", result)

    # Cas 2 : fichier absent
    result = dt.read_file.invoke({"path": "app/dashboard/page.tsx"})
    show("Fichier absent — que voit le LLM ?", result)

    # Cas 3 : fichier volumineux (tronqué à 8000 chars)
    big_content = "x" * 9000
    dt.write_file.invoke({"path": "big_file.ts", "content": big_content})
    result = dt.read_file.invoke({"path": "big_file.ts"})
    show(f"Fichier volumineux (9000 chars) — tronqué à 8000 ?", result[:120] + "...")

    note("QUESTION : pourquoi limiter à 8000 chars ?")
    note("          Car le LLM a une fenêtre de contexte limitée.")
    note("          Un fichier trop long réduit la place pour ses propres réponses.")


# ════════════════════════════════════════════════════════════════════════════
# OUTIL 3 — list_directory
# ════════════════════════════════════════════════════════════════════════════

def test_list_directory():
    sep("OUTIL 3 : list_directory(path='.')")
    note("Le LLM liste un dossier pour savoir quels fichiers existent déjà.")

    # Racine du projet sandbox
    result = dt.list_directory.invoke({"path": "."})
    show("Racine du projet sandbox", result)

    # Sous-dossier
    result = dt.list_directory.invoke({"path": "app"})
    show("Sous-dossier app/", result)

    # Dossier absent
    result = dt.list_directory.invoke({"path": "components"})
    show("Dossier absent — que voit le LLM ?", result)

    note("OBSERVATION : les [DIR] sont listés avant les [FILE].")
    note("             Le LLM peut ainsi savoir quelle structure existe.")


# ════════════════════════════════════════════════════════════════════════════
# OUTIL 4 — shell_exec
# ════════════════════════════════════════════════════════════════════════════

def test_shell_exec():
    sep("OUTIL 4 : shell_exec(command)")
    note("L'outil le plus puissant — et le plus risqué.")
    note("Le LLM lance des vraies commandes shell dans le dossier projet.")

    # Cas 1 : commande simple qui réussit
    result = dt.shell_exec.invoke({"command": "echo 'test depuis le LLM'"})
    show("echo simple (exit 0)", result)

    # Cas 2 : commande qui échoue
    result = dt.shell_exec.invoke({"command": "cat fichier_inexistant.txt"})
    show("Fichier inexistant → exit code non-zéro", result)

    # Cas 3 : commande interactive bloquée
    result = dt.shell_exec.invoke({"command": "npm init"})
    show("Commande interactive bloquée (npm init sans -y)", result)

    # Cas 4 : tentative d'écriture dans un fichier protégé via shell
    dt.set_protected_files(["app/layout.tsx"])
    result = dt.shell_exec.invoke({"command": "echo '<html>' > app/layout.tsx"})
    show("Redirection shell vers fichier protégé", result)
    dt.set_protected_files(None)

    # Cas 5 : lister les fichiers (commande utile pendant un run)
    result = dt.shell_exec.invoke({"command": "ls -la app/"})
    show("ls -la app/ (ce que le LLM utilise pour s'orienter)", result)

    note("QUESTION IMPORTANTE : shell_exec a un timeout de 120s.")
    note("Si npm install ou npm run build dépasse 120s → TIMEOUT.")
    note("Le LLM voit 'TIMEOUT' et ne sait pas si la commande a partiellement réussi.")


# ════════════════════════════════════════════════════════════════════════════
# OUTIL 5 — file_exists
# ════════════════════════════════════════════════════════════════════════════

def test_file_exists():
    sep("OUTIL 5 : file_exists(path)")
    note("Outil léger — le LLM vérifie si un fichier existe avant d'écrire.")

    result = dt.file_exists.invoke({"path": "app/page.tsx"})
    show("app/page.tsx (créé en outil 1)", result)

    result = dt.file_exists.invoke({"path": "app/dashboard/page.tsx"})
    show("app/dashboard/page.tsx (jamais créé)", result)

    result = dt.file_exists.invoke({"path": "package.json"})
    show("package.json (absent dans le sandbox)", result)

    note("Le LLM utilise file_exists pour décider s'il doit créer ou modifier.")


# ════════════════════════════════════════════════════════════════════════════
# SYNTHÈSE
# ════════════════════════════════════════════════════════════════════════════

def print_synthesis():
    sep("SYNTHÈSE — Ce que ces 5 outils révèlent")
    print("""
  Le LLM du dev agent ne voit QUE des chaînes de texte.
  Il n'a pas accès au disque directement — tout passe par ces outils.

  Flux d'un tour de boucle typique :
  ┌─────────────────────────────────────────────────────────┐
  │ 1. LLM appelle list_directory(".")                      │
  │    → voit quels fichiers existent                       │
  │ 2. LLM appelle write_file("app/page.tsx", "...")        │
  │    → reçoit "OK: app/page.tsx écrit (245 chars)"        │
  │ 3. LLM appelle shell_exec("npm run build")              │
  │    → reçoit "FAILED (exit 2)\\nTS7006: Parameter..."    │
  │ 4. LLM lit l'erreur et rappelle write_file pour corriger│
  └─────────────────────────────────────────────────────────┘

  Les protections clés :
  • _safe_path()       → empêche le LLM de sortir du dossier projet
  • _protected_files   → empêche la réécriture des templates
  • interactive blocklist → empêche les commandes qui attendent une entrée
  • timeout 120s       → empêche les boucles infinies

  Ce qui n'est PAS protégé :
  • shell_exec("rm -rf .") → supprime tout le projet
  • shell_exec("curl ...") → peut faire des requêtes réseau
  → C'est pour ça que le container Docker isole le workdir.
""")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true", help="Ne pas supprimer le sandbox après")
    parser.add_argument("--outil", type=int, choices=[1,2,3,4,5], help="Tester un seul outil (1-5)")
    args = parser.parse_args()

    print("\n" + "═"*62)
    print("  SESSION 2 — LES OUTILS DU DEV AGENT")
    print("  Ce que le LLM peut faire et ce qu'il reçoit en retour")
    print("═"*62)

    setup_sandbox()

    try:
        tests = {
            1: test_write_file,
            2: test_read_file,
            3: test_list_directory,
            4: test_shell_exec,
            5: test_file_exists,
        }

        if args.outil:
            tests[args.outil]()
        else:
            for fn in tests.values():
                fn()

        print_synthesis()

    finally:
        if not args.keep:
            teardown_sandbox()
        else:
            print(f"\n  Sandbox conservé : {SANDBOX}")

    print("\n" + "═"*62)
    print("  FIN SESSION 2")
    print("  Questions à noter : voir les 💡 dans la sortie ci-dessus")
    print("═"*62 + "\n")


if __name__ == "__main__":
    main()
