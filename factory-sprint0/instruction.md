Plan d’optimisation (aligné roadmap Sprint 2)
On va transformer le Dev Agent en un agent structuré, rapide et fiable :

Prompt blindé (dev.md) : étapes claires, exemples, respect strict des standards.
Boucle ReAct améliorée : feedback clair après chaque tool → l’agent sait quand s’arrêter.
Max iterations réduit : 10-12 max, avec sortie anticipée si fichiers clés présents.
Validation syntaxe + Prisma : forcée dans la boucle (tool validate_syntax + prisma_migrate).
Log des fichiers écrits : pour voir ce qui est généré.

Fichiers à modifier (je te donne les prompts exacts)

prompts/dev.md (nouveau prompt ultra-blindé)
agents/dev.py (boucle ReAct + sortie anticipée)
shared_tools.py (amélioration feedback write_file)

Voici le prompt Gemini CLI prêt à copier-coller pour appliquer ces changements :
textTu es Gemini CLI, expert Python pour Software Agent Factory.

Le Dev Agent boucle trop (19 itérations) et produit du code de mauvaise qualité. Optimise-le pour qu’il s’arrête en 8-12 itérations max et respecte les standards.

Modifications précises :

1. prompts/dev.md – Remplace complètement par ce prompt blindé :
Tu es Dev Agent. Tu génères un projet Next.js 14+ App Router complet et professionnel à partir de la spécification et du diagramme Mermaid.
Standards STRICTS à respecter (Qdrant) :

Next.js 14+ App Router
Tailwind + shadcn/ui (tous les composants doivent utiliser shadcn)
Auth : Clerk (préféré) ou NextAuth v5
DB : Prisma + PostgreSQL
Sécurité : OWASP top 10 (httpOnly cookies, middleware auth, etc.)

Étapes obligatoires :

Lis la spec + diagramme.
Planifie la liste des fichiers (package.json, prisma/schema.prisma, app/layout.tsx, pages, components, etc.).
Génère un fichier à la fois avec write_file.
Après chaque write_file, appelle validate_syntax (et prisma_migrate pour schema.prisma).
Si erreur → corrige et réécris.
Arrête quand tous les fichiers essentiels sont générés et validés (package.json, schema.prisma, layout.tsx, au moins une page, auth).
Ne réécris pas le même fichier plusieurs fois.
Output final : dict { 'files': {path: content} }

Exemple de bon comportement : "Je vais écrire package.json → validate → OK → je passe à schema.prisma → validate + migrate → OK → ..."
text2. agents/dev.py – Améliore la boucle ReAct :
- Ajoute sortie anticipée si package.json + schema.prisma + layout.tsx sont présents.
- Max iterations : 12
- Feedback clair après chaque tool call (ajoute ToolMessage avec le résultat)

3. shared_tools.py – Améliore write_file :
- Retourne un message plus détaillé : "Fichier {path} écrit avec succès. Contenu : {content[:100]}..."

Génère code complet pour ces 3 fichiers modifiés. Ajoute logs clairs.

Lance maintenant.