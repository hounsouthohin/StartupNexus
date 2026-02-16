# EVALUATOR_SPEC.md  
**Software Agent Factory — Système d'évaluation qualité des runs**  
Version: 1.0 – Sprint C1 – Février 2026  

## Objectif principal

L’**EvaluatorAgent** analyse les historiques de runs du LearnerAgent pour :  
- Calculer un **score de qualité global** par run (0–100)  
- Détecter les **patterns d’échecs récurrents** (avec seuil configurable)  
- Produire des recommandations actionnables (nouveaux standards, ajustements de prompts, etc.)  
- Alimenter automatiquement la boucle d’auto-amélioration (via upsert dans Qdrant)

## 1. Métriques de qualité (scoring run individuel)

Chaque run est évalué sur un score total de **100 points**, répartis comme suit :

| Métrique                  | Poids | Description / Critères                                                                 | Score max | Condition pour score plein | Pénalité typique |
|---------------------------|-------|----------------------------------------------------------------------------------------|-----------|----------------------------|------------------|
| `build_success`           | 30    | Build Next.js + Prisma migrate réussit sans erreur                                    | 30        | success = true             | -30 si échec     |
| `files_count`             | 15    | Nombre de fichiers générés (attendu 8–25 pour un SaaS moyen)                          | 15        | ≥ 12 fichiers              | linéaire < 12    |
| `clerk_compliant`         | 20    | Authentification via Clerk v5+ (middleware, UserButton, pas de custom auth)           | 20        | clerk_compliant = true     | -20 si absent    |
| `security_standards`      | 15    | Présence validation Zod + headers sécurité + ownership check sur API routes           | 15        | security_standards = true  | -15 si échec     |
| `qa_e2e_coverage`         | 10    | Nombre de tests E2E Playwright générés (cible ≥ 4–6)                                   | 10        | ≥ 5 tests                  | linéaire < 5     |
| `dev_test_coverage`       | 10    | Couverture de tests unitaires Jest (pourcentage lines/functions)                       | 10        | ≥ 80%                      | linéaire < 80%   |

**Score total** = somme pondérée (0–100)  
**Score moyen** sur N runs = moyenne pondérée des scores individuels  
**Taux d’échec global** = 1 – (score_moyen / 100)

## 2. Détection de patterns d’échecs

Un **pattern** est considéré comme significatif quand :

- **Récurrence minimale** : ≥ 3 occurrences (configurable : `--min-recurrence`)  
- **Taux d’apparition** : ≥ 10% des runs analysés (configurable : `--min-failure-rate`)  
- **Signature unique** : combinaison métrique + type d’erreur (ex: `dev_test_run:error:no_files_generated`)

### Exemples de signatures typiques

- `build_success:error:sharp_not_installed`  
- `qa_run:error:no_e2e_tests_generated`  
- `clerk_compliant:error:missing_middleware`  
- `security_standards:error:unsafe_direct_prisma_query`  
- `files_count:error:too_few_files`  

## 3. Format exact de `patterns_report.json`

```json
{
  "generated_at": "2026-02-15T18:50:23.123456Z",
  "log_source": "logs/shadow/learner_shadow_log.json",
  "total_runs": 142,
  "avg_quality_score": 68.4,
  "global_failure_rate": 31.6,
  "scoring_weights": {
    "build_success": 30,
    "files_count": 15,
    "clerk_compliant": 20,
    "security_standards": 15,
    "qa_e2e_coverage": 10,
    "dev_test_coverage": 10
  },
  "patterns_detected": 7,
  "patterns": [
    {
      "pattern_id": "P-001",
      "signature": "dev_test_run:error:no_files_generated",
      "occurrences": 18,
      "failure_rate": 12.68,
      "metrics": { "dev_test_run": 18 },
      "sample_projects": ["taskflow", "crm-mini", "invoice-pro", ...],
      "sample_errors": ["No code generated due to LLM hallucination", ...],
      "recommendation": "Ajouter un standard obligatoire : vérification minimale de 8 fichiers avant commit",
      "priority": "HIGH"
    },
    {
      "pattern_id": "P-002",
      "signature": "qa_run:error:no_tests_generated",
      "occurrences": 11,
      "failure_rate": 7.75,
      "metrics": { "qa_run": 11 },
      "sample_projects": ["taskflow", "blog-platform", ...],
      "sample_errors": ["LLM n'a pas respecté le format JSON attendu", ...],
      "recommendation": "Renforcer le prompt QA avec exemple JSON strict et validation Zod",
      "priority": "MEDIUM"
    },
    ...
  ],
  "min_recurrence_threshold": 3,
  "min_failure_rate_threshold": 0.10
}



5. Recommandations automatiques suggérées
Pour chaque pattern détecté, l’EvaluatorAgent doit produire une recommandation dans l’une des catégories suivantes :

Nouveau standard factory → upsert dans factory_standards (LearnerAgent)
Ajustement de prompt → modifier le prompt système de l’agent concerné
Ajout de validation contrat → renforcer le JSON schema de l’agent
Boucle de retry ou fallback → ajouter une étape de correction automatique
Alerte humaine → pattern critique non résolu après X runs

Exemple :
"Ajouter standard : 'Toujours inclure sharp dans package.json pour Vercel image optimization'"
6. Intégration future dans la boucle
textRun LearnerAgent
   ↓
Append metrics au shadow log
   ↓
Exécute evaluator.py (cron / post-run hook)
   ↓
Si patterns HIGH priority → déclenche LearnerAgent en mode "standard_generation"
   ↓
Nouveaux standards → upsert Qdrant → amélioration automatique des runs suivants
7. Commandes utiles
Bash# Analyse basique
python evaluator.py

# Plus strict
python evaluator.py --min-recurrence 5 --min-failure-rate 0.15