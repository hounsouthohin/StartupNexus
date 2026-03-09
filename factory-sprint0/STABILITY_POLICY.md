# Stability Policy — Sprint A (Freeze Contrôlé)

## Branche active : `stabilization`

Toute modification de code doit passer par la branche `stabilization`.
Aucun merge direct sur `main` pendant Sprint A.

---

## Règle de merge

**Autorisé sur `stabilization`** :
- Tickets P0 uniquement (T001→T006, T010, T013)
- Hotfixes bloquants sur le pipeline existant
- Corrections de guards (`_prebuild_gates`, `_requirements_gate`)

**Interdit pendant Sprint A** :
- Nouveaux agents ou nouveaux outils LLM
- Nouvelles stacks (→ Sprint C)
- Optimisations de prompt non liées à un guard (→ Sprint D)
- Refactoring non lié à la stabilisation

---

## Checklist avant merge vers `stabilization`

- [ ] Le ticket est P0 ou P1 (défini dans plan.md)
- [ ] Le changement a un DoD mesurable
- [ ] Un run d'observation a été effectué (lire sorties.md)
- [ ] Aucune régression sur les guards existants

---

## Ordre d'exécution Sprint A

| Ordre | Ticket | Description | Dépend de |
|-------|--------|-------------|-----------|
| 1 | T000-B | Fix normalisation `\n` ciblée | — |
| 2 | T000-BL | Baseline métriques 5 runs | — |
| 3 | T001 | **CE DOCUMENT** — Freeze + branche | — |
| 4 | T002 | Requirements Engine unifié | T001 |
| 5 | T003 | Alignement spec_coverage | T002 |
| 6 | T004 | State Machine déterministe + budget token | T001 |
| 7 | T005 | Final Status Tool-Driven | T004 |
| 8 | T006 | Contrats Erreur/Sortie alignés | T001 |
| 9 | T010 | Guards Constructifs (templates) | T004 |
| 10 | T013 | Regression Test Pack | T003, T005, T006 |

---

## KPIs à atteindre en fin Sprint A

| Métrique | Avant | Cible |
|----------|-------|-------|
| `build_attempted` | ~0% | ~70% |
| `final_status coherence` | ~60% | 100% |
| `gate divergence` | élevé | 0% |
| `avg_iterations` | 14 | 8-10 |

Référence : `factory-sprint0/logs/metrics/baseline_kpis.json`
