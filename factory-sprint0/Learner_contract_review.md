# LEARNER_CONTRACT_REVIEW.md  
**Software Agent Factory — Revue du contrat LearnerAgent**  
Version: 1.0 – Sprint C2 – Février 2026  
Auteur: Grok (review pour Sprint 2)

## Objectif de cette revue

Analyser si le contrat actuel de **LearnerAgent** (shadow mode Sprint 2–3) permet de collecter  
toutes les données nécessaires à l’**EvaluatorAgent** pour :

- Calculer le score de qualité pondéré (build_success, files_count, clerk_compliant, etc.)
- Détecter les patterns d’échecs récurrents
- Produire des suggestions de standards fiables
- Alimenter le shadow log de manière exploitable

## Évaluation globale du contrat actuel

**Points forts :**  
- Structure claire input/output/error/health  
- Input contient déjà les éléments clés du run (project_name, specification, generated_files, run_metrics)  
- Output bien orienté shadow : suggestions + confidence + rationale + human_review  
- shadow_log_entry intégré dans l’output → facile à append dans learner_shadow_log.json  

**Points faibles / manques critiques pour l’EvaluatorAgent :**  
Le contrat ne collecte **pas assez de métriques granulaires** pour calculer le score de qualité 100 pts décrit dans EVALUATOR_SPEC.md.

| Métrique requise par EvaluatorAgent | Présente dans input_schema actuel ? | Commentaires / Manque |
|-------------------------------------|--------------------------------------|------------------------|
| build_success                       | Non                                  | Critique – poids 30 pts |
| total_files                         | Non (seulement generated_files)      | Peut être déduit, mais pas explicite |
| clerk_compliant                     | Non                                  | Critique – poids 20 pts |
| security_standards                  | Non                                  | Critique – poids 15 pts |
| generated_tests_count (E2E)         | Oui (via e2e_tests, mais indirect)   | Manque le compte explicite |
| test_coverage_pct (Jest)            | Non                                  | Critique – poids 10 pts |
| qa_duration_seconds                 | Oui (dans run_metrics)               | OK |
| intervention_count / retry_count    | Oui                                  | OK, utile pour robustesse |

**Verdict rapide :**  
Le contrat est **suffisant pour collecter les suggestions et les métriques temporelles**,  
mais **insuffisant** pour calculer le score pondéré complet et détecter finement les patterns  
(build, clerk, security, coverage).

## Modifications proposées pour Sprint 2

### A. Améliorations input_schema (données collectées du run)

Ajouter ces champs obligatoires ou fortement recommandés dans `run_metrics` :

```json
"run_metrics": {
  "type": "object",
  "required": ["total_duration_seconds", "status", "build_success", "clerk_compliant"],
  "properties": {
    // Champs existants conservés
    "total_duration_seconds": { ... },
    "status": { ... },

    // Ajouts critiques pour scoring
    "build_success": {
      "type": "boolean",
      "description": "true si next build + prisma migrate deploy OK"
    },
    "clerk_compliant": {
      "type": "boolean",
      "description": "true si auth via Clerk middleware + UserButton + pas de custom auth"
    },
    "security_standards_compliant": {
      "type": "boolean",
      "description": "true si Zod + headers sécurité + ownership check détectés"
    },
    "total_files_generated": {
      "type": "integer",
      "minimum": 0,
      "description": "Nombre total de fichiers écrits (déduit de generated_files)"
    },
    "e2e_tests_count": {
      "type": "integer",
      "minimum": 0,
      "description": "Nombre de fichiers de tests E2E générés"
    },
    "unit_test_coverage_pct": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Couverture Jest lines/functions (si mesurée)"
    },

    // Optionnel mais utile
    "warnings_count": { "type": "integer", "minimum": 0 },
    "llm_tokens_used": { "type": "integer", "minimum": 0 }
  }
}


B. Améliorations output_schema (shadow log + suggestions)

Ajouter un champ quality_score dans analysis_summary pour stocker le score calculé
Rendre suggested_standards plus riche pour l’évaluation future :

JSON"suggested_standards": {
  "items": {
    "properties": {
      // Champs existants
      "text": { ... },
      "metadata": { ... },
      "confidence_score": { ... },
      "rationale": { ... },

      // Ajouts pour évaluation & priorisation
      "pattern_signature": {
        "type": "string",
        "description": "Signature du pattern détecté (ex: dev_test_run:error:no_files_generated)"
      },
      "failure_impact": {
        "type": "number",
        "minimum": 0,
        "maximum": 30,
        "description": "Impact estimé sur le score qualité (pts perdus)"
      },
      "priority": {
        "type": "string",
        "enum": ["HIGH", "MEDIUM", "LOW"]
      }
    }
  }
}

Dans analysis_summary ajouter :

JSON"analysis_summary": {
  "properties": {
    // existants
    "quality_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Score qualité calculé pour ce run (0-100)"
    },
    "score_breakdown": {
      "type": "object",
      "properties": {
        "build_success": { "type": "number" },
        "files_count": { "type": "number" },
        // etc. pour toutes les métriques
      }
    }
  }
}
C. Recommandations finales pour Sprint 2



Action,Priorité,Impact sur EvaluatorAgent
Ajouter les booléens build/clerk/security dans run_metrics,Haute,Permet scoring 65/100 pts
Ajouter total_files_generated + e2e_tests_count,Haute,Scoring complet + patterns
Ajouter quality_score + breakdown dans output,Moyenne,Shadow log auto-évalué
Ajouter pattern_signature dans suggestions,Moyenne,Meilleure traçabilité

Conclusion :
Le contrat actuel est un bon squelette shadow, mais manque ~50 % des métriques nécessaires pour un scoring fiable et une détection de patterns précise.
Avec les ajouts ci-dessus, il deviendra pleinement compatible avec EVALUATOR_SPEC.md et permettra une boucle d’amélioration autonome dès Sprint 3–4.
Prochaines étapes suggérées :

Mettre à jour learner_agent_contract.json avec ces champs
Tester un run shadow complet → vérifier que shadow_log_entry contient tout
Lancer evaluator.py dessus → valider que patterns_report.json est riche

Fin de la revue – Sprint 2 prêt à implémenter ces évolutions.
text