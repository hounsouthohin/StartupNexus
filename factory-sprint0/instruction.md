Tu es un ingénieur senior Python dans une startup full-agents IA où ces outils sont appelés des centaines de fois par jour dans des boucles ReAct critiques. Performance et fiabilité sont prioritaires.

Ton objectif : modifier le fichier shared_tools.py pour qu’il soit **10x plus performant et 100% fiable** en appliquant **exactement** ces changements :

1. rag_search :
   - Initialiser QdrantClient et OpenAIEmbeddings **globalement** (au niveau module) pour réutilisation sur tous les appels (singleton pattern).
   - Ajouter try/except complet : en cas d’erreur (connexion, API, etc.) retourner "Aucun résultat (erreur de recherche)".
   - Ajouter un cache LRU (from functools import lru_cache) avec maxsize=50 pour éviter re-embeddings identiques.

2. write_file :
   - Valider que l’encoding est UTF-8 (ajouter encoding='utf-8' dans open).
   - Ajouter check : if os.path.isabs(path): return erreur "Chemins absolus interdits pour sécurité".
   - Conserver le mode "w" (overwrite) mais ajouter un log si le fichier existait déjà.

3. validate_syntax :
   - Ajouter timeout=30 sur tous les subprocess.run (timeout=30).
   - Étendre la couverture : supporter .js, .ts, .tsx avec les mêmes règles ESLint (pas besoin de règles dynamiques si compliqué, juste ajouter les extensions).
   - Améliorer le message d’erreur avec le code retour.

4. prisma_migrate :
   - Générer un nom de migration unique : 'init_' + datetime.now().strftime("%Y%m%d_%H%M%S")
   - Ajouter une vérification préalable : exécuter 'npx prisma migrate status --schema <path>' pour détecter si déjà appliqué (si "Applied" → skip ou log warning).
   - Ajouter timeout=60 sur subprocess.

Règles générales :
- Ne pas casser les signatures existantes des outils (args_schema, return type).
- Conserver le style docstring actuel et l’améliorer légèrement (ajouter exemples si possible).
- Ajouter des commentaires clairs sur les changements.
- Tester mentalement chaque outil (scénarios : succès, erreur connexion, fichier existant, migration déjà appliquée).
- Ne pas ajouter de dépendances externes sauf celles déjà présentes.

Output : le fichier shared_tools.py **modifié en entier**, prêt à être copié-collé.