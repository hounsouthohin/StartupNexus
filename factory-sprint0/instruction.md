Tu es Gemini CLI, expert Python pour Software Agent Factory.

Fixe l'erreur bloquante : Architect Agent ne produit pas JSON valide (raw response Markdown narratif sans JSON). Workflow crash avec ValueError.

Modifications précises :

1. agents/architect.py – Blindé le prompt système (prompts/architect.md ou inline) :
   - Ajoute : "Output UNIQUEMENT un JSON valide : { 'specification': 'texte Markdown complet de la spec', 'mermaid_diagram': 'code Mermaid valide (classDiagram ou flowChart) entre ```mermaid et ```' }. Pas de texte supplémentaire."
   - Implémente tool generate_mermaid_diagram dynamiquement : appel LLM séparé avec prompt "Génère Mermaid [spec] → retourne UNIQUEMENT le code Mermaid."

2. workflows/activities/architect_activity.py – Améliore parsing :
   - Si agent_result est dict avec 'specification' et 'mermaid_diagram' : OK.
   - Sinon : fallback extraction regex (find ### Spécification... pour spec ; find ```mermaid...``` pour diagramme).
   - Log l'extraction via utils.logger.
   - Retourne toujours { 'specification': str, 'mermaid_diagram': str }

3. workflows/factory_workflow.py – Ajoute retry policy basique :
   - Pour architect_activity : schedule_to_close_timeout=300, retry_policy={ 'initial_interval': timedelta(seconds=5), 'backoff_coefficient': 2.0, 'maximum_attempts': 3 }

Modifie uniquement ces 3 fichiers. Génère code complet mis à jour. Ajoute logs pour tracer.

Lance maintenant.