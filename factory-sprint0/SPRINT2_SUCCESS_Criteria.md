# SPRINT2_SUCCESS_CRITERIA.md  
**Software Agent Factory — Critères de succès Sprint 2**  
Version: 1.0 – Février 2026  

## Règle unique de fin de sprint

**Sprint 2 est terminé quand TOUS les critères ci-dessous sont validés à 100 %.**  
Pas de "presque", pas de "ça marche sur mon poste".  
Tout doit passer en CI ou via un script de validation automatisé.

## Critères obligatoires (tous doivent être vrais)

| N° | Critère                                                                 | Preuve mesurable / commande à exécuter                                 | Valeur attendue               | Automatisé ? |
|----|-------------------------------------------------------------------------|--------------------------------------------------------------------------|--------------------------------|--------------|
| 1  | Le worker Temporal démarre sans aucune erreur                          | `python run/worker.py` → reste actif > 30 s sans traceback              | 0 erreur dans les logs         | Oui (grep)   |
| 2  | Au moins 3 activities sont enregistrées correctement                   | Logs du worker contiennent les 4 noms d’activités                       | architect, dev_test, qa, github | Oui (grep)   |
| 3  | Un workflow de test minimal (phrase → spec → code → PR) se lance       | `python test_client.py` (ou temporal cli) → handle créé sans erreur    | workflow_id visible            | Oui          |
| 4  | Au moins un run complet termine en status SUCCESS                      | Vérifier dans Temporal UI ou via `temporal workflow list`              | 1 workflow avec status COMPLETED | Oui          |
| 5  | Le shadow log contient au minimum 1 entrée valide                      | `cat logs/shadow/learner_shadow_log.json` → "events" ≥ 1                | ≥ 1 événement avec timestamp   | Oui (jq)     |
| 6  | `patterns_report.json` est généré sans erreur après un run             | `python evaluator.py` → fichier créé + "patterns_detected" ≥ 0         | Fichier JSON valide            | Oui (jq)     |
| 7  | Le score qualité moyen des runs terminés est ≥ 45/100                  | Rapport evaluator → "avg_quality_score"                                 | ≥ 45.0                         | Oui          |
| 8  | Au moins 1 pattern est détecté (même avec min_recurrence=1 temporaire) | Rapport evaluator → "patterns" non vide                                 | ≥ 1 pattern                    | Oui          |
| 9  | validate_contracts.py passe sans aucun crash ni ValidationError inattendu | `python scripts/validate_contracts.py` → "TOUT EST OK ✅"              | Pas de traceback               | Oui          |
| 10 | Tous les fichiers générés dans un run contiennent la mention "généré par Factory Nexus AI" ou similaire | grep récursif dans un dossier de sortie                                 | Tous les .ts / .tsx / .py      | Oui (grep)   |
| 11 | Pas plus de 3 warnings ou erreurs critiques dans les logs du worker pendant un run complet | grep -i "error\|warning\|exception" logs/worker.log                     | ≤ 3 lignes critiques           | Oui          |
| 12 | Le temps moyen d’un run complet < 8 minutes (premier run toléré jusqu’à 12 min) | Mesuré via run_metrics.total_duration_seconds                           | Moyenne ≤ 480 s                | Oui          |

## Critères bonus (non bloquants mais très souhaitables)

- Score qualité moyen ≥ 60/100 sur les 3 derniers runs  
- Au moins 2 suggestions de standards dans `suggested_standards` avec confidence_score ≥ 0.65  
- Le repo GitHub créé contient au minimum 10 fichiers (hors README)  
- Pas d’erreur 500/timeout dans les activités pendant 3 runs consécutifs  

## Commande de validation complète (à automatiser plus tard)

```bash
# Vérification rapide manuelle
python run/worker.py & sleep 10 && pkill -f "python run/worker.py"  # teste démarrage
python scripts/validate_contracts.py
python evaluator.py
# + lancer un workflow via test_client.py ou temporal cli
# puis vérifier les logs + patterns_report.json + shadow log



Statut actuel (à remplir par Arthur à la fin du sprint)

 Critère 1 – Worker démarre
 Critère 2 – 4 activities enregistrées
 Critère 3 – Workflow lancé
 Critère 4 – Au moins 1 run SUCCESS
 Critère 5 – Shadow log ≥ 1 entrée
 Critère 6 – patterns_report.json généré
 Critère 7 – Score moyen ≥ 45
 Critère 8 – ≥ 1 pattern détecté
 Critère 9 – validate_contracts.py OK
 Critère 10 – Mention "généré par" dans les fichiers
 Critère 11 – ≤ 3 warnings/erreurs
 Critère 12 – Temps moyen < 8 min

Sprint 2 terminé quand : 12/12 cases cochées.
Date de validation : ____________________
Signature (ou commit hash) : ____________________
text