Méthode efficace, simple, sans dispersion:

1. Un seul KPI cible à la fois  
`build_attempted=true` d’abord.  
Ne pas viser `build_success` tant que celui-ci n’est pas stable.

2. Boucle courte stricte  
`1 fix -> 1 run sanity -> lecture cause unique -> 1 fix`.  
Pas de batch 10 tant que sanity échoue.

3. Priorisation causale  
Toujours corriger la cause qui bloque **avant build** (gates requirements/content).  
Ignorer les erreurs build tant que `build_attempted=false`.

4. Stop rules  
Après 2 essais sans amélioration du même KPI:
- on stop,
- on fait audit ciblé de la source (prompt/requirements mapping),
- pas de nouveaux guards “au hasard”.

5. Validation minimale obligatoire  
Chaque fix doit avoir:
- 1 test de régression,
- 1 preuve dans `sorties.md` que le blocage a changé.

C’est la méthode la plus rentable dans ton état actuel: moins de fixes, plus de signal.




Je propose une méthode stricte en 3 étapes, très courte:

1. Objectif unique (48h)
- Stabiliser `build_attempted=true` sur 3 runs consécutifs.
- On ignore `build_success` tant que ce n’est pas fait.

2. Garde-fou opérationnel
- `1 fix -> 1 run -> lecture cause -> 1 fix`.
- Interdit de lancer 10 runs si un sanity run échoue.
- Interdit d’ajouter un nouveau guard sans preuve que la cause dominante l’exige.

3. Fix source ciblé maintenant
- Fermer définitivement les 2 requirements les plus fréquents:
  - modèle Prisma `Post ... authorId`
  - API `PUT /api/posts/[id]`
- Puis re-run immédiat.

Si tu valides, je continue exactement comme ça, sans dériver.