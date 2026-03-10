Analyse du run
Ce qui a changé — progrès massifs
Signal	Avant les fixes	Ce run
Architect spec valide	❌ spec générique hors-stack	✅ spec_validation_status: "OK"
spec_coverage	—	✅ 1.0 — 6/6 requirements couverts
Clerk compliant	—	✅ clerk_compliant: true
Semantic violations	—	✅ 0
QA exécuté	❌ jamais (NameError)	✅ 1 test généré
GitHub exécuté	❌ jamais	✅ PR créé
Learner exécuté	❌ jamais	✅ 10 suggestions
Tous les agents	❌ pipeline mort à QA	✅ 5/5 activités complétées
Le pipeline fonctionne de bout en bout pour la première fois.

Le seul blocage restant — erreur Prisma import
build_success: false — 1 seule cause, 4 fichiers touchés :


import { prisma } from '@/lib/prisma'   ← ce que le LLM génère (named import)
import prisma from '@/lib/prisma'        ← ce qu'il faut (default import)
Next.js le dit clairement dans l'erreur :


Did you mean to use 'import prisma from "@/lib/prisma"' instead?
Le LLM a reçu ce message 14 fois sur 6 tentatives de build — et n'a pas corrigé. C'est exactement l'auto-fix déterministe que Codex recommandait.

Deux corrections à faire — rapides
Fix 1 — Préventif : ajouter dans rules_dev.md


### PRISMA CLIENT — IMPORT CRITIQUE
- TOUJOURS importer Prisma en default import : `import prisma from '@/lib/prisma'`
- INTERDIT : `import { prisma } from '@/lib/prisma'` (named import — TypeScript error)
Fix 2 — Auto-fix déterministe dans shared_tools.py ou dev_test_agent.py

Après chaque build failed avec root_cause_category = "prisma_import", scanner tous les fichiers générés et remplacer automatiquement avant le prochain build :


def _autofix_prisma_import(files: dict[str, str]) -> dict[str, str]:
    """Auto-fix déterministe : named import → default import Prisma."""
    fixed = {}
    for path, content in files.items():
        fixed[path] = content.replace(
            "import { prisma } from '@/lib/prisma'",
            "import prisma from '@/lib/prisma'"
        ).replace(
            'import { prisma } from "@/lib/prisma"',
            'import prisma from "@/lib/prisma"'
        )
    return fixed
Priorité
Fix 1 seul suffit pour le prochain run (préventif, empêche l'erreur). Fix 2 est le filet de sécurité si le LLM régresse malgré la règle.

On applique les deux ?

ok l'auto-fix deterministe , je pensais qu'on avait prévu cela dans notre roadmap3.01 ,peux tu verifier si on a un genre d'idée dans la roadmap?
Globpattern: "factory-sprint0/**/*roadmap*"
No files found
Globpattern: "*.md"
Found 50 files
Grep "auto.?fix|autofix|déterministe|deterministe|prisma.*import|import.*prisma" (in c:\Users\BAMBARA Arthur\Desktop\StartupNexus\Roadmap3.0.1.md)
2 lines of output
Grep "auto.?fix|autofix|déterministe|deterministe|prisma.*import|import.*prisma" (in c:\Users\BAMBARA Arthur\Desktop\StartupNexus\Roadmap3.0.1.md)
23 lines of output
Grep "fix.*build|build.*fix|sanitizer|patch|rewrite.*error|error.*rewrite|_fix_" (in c:\Users\BAMBARA Arthur\Desktop\StartupNexus\Roadmap3.0.1.md)
154 lines of output
Grep "sanitizer|_fix_|_ensure_|_remove_" (in c:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\config\stacks\nextjs-clerk-prisma.json)
1 line of output
Grep "sanitizer|_fix_prisma|_fix_|clerk_middleware|remove_pages" (in c:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\agents\shared_tools.py)
50 lines of output
Oui, c'est déjà prévu et même partiellement implémenté. Voici ce que j'ai trouvé.

Ce qui existe déjà dans le projet
Le concept s'appelle "Pre-build hooks" dans le code et "SanitizerRegistry" dans la roadmap.

shared_tools.py contient déjà 4 sanitizers du même type :

Fonction	Ce qu'elle corrige
_remove_pages_tests_router_conflicts()	Supprime les fichiers pages/ qui conflictuent avec App Router
_fix_nextconfig_security_headers()	Corrige le format headers() de next.config.js
_ensure_nextconfig_eslint_ignore()	Injecte eslint.ignoreDuringBuilds
_ensure_layout_html_body()	Assure les balises <html>/<body> dans layout.tsx
Tous sont appelés dans run_build() ligne 829-842 avant chaque tentative de build :


# Pre-build hooks
removed = _remove_pages_tests_router_conflicts(project_path)
if _fix_nextconfig_security_headers(project_path):
    _mutations.append("next.config.js: headers format corrigé")
if _ensure_layout_html_body(project_path):
    ...
Ce que dit la Roadmap3.0.1
La roadmap l'identifie sous deux angles :

Issue #30 — SanitizerRegistry Sprint 6-7 : formalisation de ce pattern en classes nommées déclarées dans le JSON (la version industrialisée)
Issue #31 — _fix_nextconfig_security_headers comme exemple de bug class corrigé par sanitizer dès Sprint 2
Conclusion
Ajouter le fix Prisma suit exactement le même pattern déjà en place :


# À ajouter dans shared_tools.py
def _fix_prisma_named_import(project_path: str) -> bool:
    """Corrige import { prisma } → import prisma (named → default)."""
    ...

# À appeler dans run_build() pre-build hooks
if _fix_prisma_named_import(project_path):
    _mutations.append("prisma import: named → default corrigé")
C'est du Sprint 2 (fix immédiat) — même catégorie que les issues #31 et #32. Pas besoin d'attendre Sprint 6-7 pour le SanitizerRegistry. On l'ajoute maintenant comme sanitizer ad-hoc, et il sera naturellement migré dans le Registry plus tard.

On l'implémente ?

