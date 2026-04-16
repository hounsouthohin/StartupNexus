#### Le système prompt donne une checklist de fichiers à créer, mais aucune checklist d'imports.

#### le LLM écrit 15 fichiers d'affilée, sans vérification intermédiaire. Ce n'est qu'à l'étape 2 (tsc --noEmit) que l'erreur remonte — mais à ce stade le LLM a déjà "oublié" ce qu'il a écrit dans les premiers fichiers. Sa fenêtre de contexte est occupée par les fichiers récents. : tsc apres chaque fichier critique


#### LLM génère javascript mental : Le problème dans ta startup : la stack impose "strict": true dans tsconfig.json. Ce mode refuse tout paramètre sans type explicite. Le LLM ne "ressent" pas cette contrainte pendant qu'il écrit — il ne découvre l'erreur que quand tsc tourne.

Le comportement adéquat dans cette logique : le LLM devrait, pour chaque callback ou fonction, écrire :


items.map((card: Card) => <div>{card.title}</div>)
Le système prompt ligne 200 dit "use client" OBLIGATOIRE mais il ne dit nulle part "tout paramètre de fonction DOIT avoir un type TypeScript explicite". C'est un trou dans les règles absolues. Le _TS_FIX_HINTS dans prebuild_pipeline.py (ligne 50) a des hints de réparation pour TS7006, mais ce sont des hints post-erreur, pas des instructions préventives dans le prompt de génération.



#####  Property 'id' does not exist on type 'never' : C'est la plus mécanique des trois, et la plus révélatrice.

Elle vient du workflow en deux temps. Regarde l'étape 1b du prompt (ligne 170) :


1b. Génère le client Prisma OBLIGATOIRE :
    shell_exec("npx prisma generate")
    ⚠️ Ne JAMAIS passer à l'étape 2 si prisma generate a échoué.
prisma generate crée les types TypeScript pour tes modèles. Sans ça, TypeScript ne sait pas ce que retourne prisma.board.findMany() → il infère never[] → accéder à .id sur never est impossible.

La limite : le LLM peut passer à l'étape 2 (tsc --noEmit) même si prisma generate a échoué ou été sauté. Le prompt dit "⚠️ Ne JAMAIS" mais c'est une instruction textuelle, pas une gate déterministe. Rien dans le code ne bloque physiquement le LLM de continuer si prisma generate retourne FAILED.

Le vrai flow cassé ressemble à ça :


LLM → shell_exec("npx prisma generate")
    → "FAILED (exit 1) — schema.prisma invalide"
LLM → (ignore ou mal lit l'erreur)
LLM → shell_exec("npx tsc --noEmit")
    → "prisma.board: type 'never'"  ← conséquence, pas cause
LLM → essaie de corriger app/page.tsx pendant 5 tours
    → corrige le mauvais fichier, le vrai problème est schema.prisma


### read_file limité à 8000 chars :  
    La truncation est brute. Voici le code exact :


if len(content) > 8000:
    return content[:8000] + f"\n... [tronqué — {len(content)} chars total]"
Ce qui manque et que les agents de production ont :

Technique	Notre factory	Claude Code / Codex
Read par plage de lignes	❌ absent	✅ view file:10-50
Extraction AST (juste la fonction)	❌ absent	✅ tree-sitter
Résumé sémantique du fichier	❌ absent	✅ summarization node
Offset / pagination	❌ absent	✅
C'est une vraie dette. Un fichier app/page.tsx peut facilement dépasser 8000 chars dans un projet complexe. Le LLM voit une version tronquée et écrit une correction basée sur un contexte incomplet → régression.


3. LangGraph pour contexte total — déjà utilisé, mais insuffisamment
La factory utilise déjà LangGraph (StateGraph dans dev_graph.py). Le DevState maintient :


class DevState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]  # s'accumule
    spec: dict
    build_attempts: int
    last_build_error: str
    error_signatures: List[str]  # détection de boucle
    ...
Ce qui est fait : les messages s'accumulent tour après tour. La détection de boucle (error_signatures avec hash MD5) évite que le LLM répète la même erreur à l'infini.

Ce qui manque : un nœud de compression de contexte. Après 10 tours, l'historique des messages contient des dizaines de ToolMessage verbeux ("OK: app/page.tsx écrit (3421 chars)"). Ce bruit occupe le contexte et pousse les messages importants hors fenêtre.

Ce qu'il faudrait :


[messages trop longs] → nœud summarize_context → [résumé compact : "fichiers écrits : X, Y, Z / dernière erreur : TS7006 dans page.tsx"]
Ni implémenté, ni planifié actuellement.

4. Windows vs Linux
Pas un problème en pratique — shell_exec tourne dans le container Docker Linux, pas sur ta machine Windows. Le container est Ubuntu, les commandes ls, cat, npx sont toutes Linux.

Problème potentiel : si quelqu'un fait tourner la factory hors Docker sur Windows → tout explose. Aucune protection contre ça dans le code actuel.

5. Interactive commands — force flags
Ce qui est implémenté (dev_tools.py ligne 189) :


_INTERACTIVE_BLOCKLIST = (
    "create-config", "eslint --init", "npm init",
    "npx init", "prisma init", "next telemetry",
)
Ce qui manque :

Auto-injection de -y sur les commandes npm (npm install x → npm install x --yes)
CI=true dans l'environnement (désactive les prompts interactifs de beaucoup d'outils)
DEBIAN_FRONTEND=noninteractive pour apt
Détection générique "cette commande attend stdin" → blocage avant timeout
Claude Code fait ça : il injecte CI=true dans tout subprocess et force -y/--yes systématiquement.

6. Terminal Emulation
Non implémenté. La factory utilise :


subprocess.run(command, shell=True, capture_output=True, ...)
capture_output=True = pas de TTY. Certains outils détectent l'absence de TTY et se comportent différemment (couleurs désactivées, prompts supprimés, formats modifiés).

Pour les cas critiques (npm, prisma), ça fonctionne. Mais pour des outils plus complexes qui requièrent une interaction PTY, ce serait bloquant.


7. Timeouts — état réel
Commande	Timeout actuel	Type
npm install (pre-run)	300s hardcodé	Synchrone bloquant
prisma generate (pre-run)	120s hardcodé	Synchrone bloquant
shell_exec LLM	120s hardcodé	Synchrone bloquant
prebuild_pipeline	120s par stage	Synchrone bloquant
Ce qui manque :

BATCH_MAX_TIMEOUT_MS configurable par type de commande
Exécution async + polling ("est-ce que npm install est fini ?")
Streaming stdout pendant un long build (le LLM voit le progrès en temps réel)
Timeout graduel : warning à 80s, kill à 120s
Production agents : shell_exec en streaming. Le LLM voit les lignes au fur et à mesure, peut décider d'annuler si la sortie lui apprend que c'est parti dans le mauvais sens.


8. Feedback loop & Security sandboxing
Feedback loop — ce qui existe :

Prebuild gate bloque le build si violations TSC/ESLint
Anti-loop par hash d'erreur (error_signatures)
Message d'injection si même erreur ≥ 2 fois
Ce qui manque :

Streaming : le LLM attend que la commande finisse avant de voir quoi que ce soit
Attribution : "ce fichier que tu as modifié a causé cette régression"
Feedback par fichier : après chaque write_file, valider immédiatement avec tsc
Sandboxing — ce qui existe :

Docker isole le container
_safe_path() bloque le path traversal
_protected_files protège les templates
Blocklist interactive
Ce qui manque :

Isolation réseau (le container peut faire des requêtes HTTP arbitraires)
Limites CPU/mémoire non définies dans le code (dépend de la config Docker externe)
Pas de rollback si le LLM corrompt un fichier existant