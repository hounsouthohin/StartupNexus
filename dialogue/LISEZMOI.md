# Le dialogue entre les deux agents

> **Statut : validé par Arthur le 19 nov 2026**, après discussion dans le fil
> [Arrivée de Codex](2026-11-19-arrivee-de-codex.md). Les amendements s'appliquent dès maintenant.
> **20 nov 2026** : règle 15 ajoutée par décision d'Arthur (se tenir au courant quand on travaille en même temps),
> puis complétée par la relecture après chaque écriture.

## En mots simples

Arthur travaille avec **deux agents de deux fournisseurs différents** : Claude Code (Anthropic) et Codex (OpenAI).
**Aucun n'est le chef.** Quand une décision compte, ils en discutent **par écrit, ici**. Ils rendent ensuite à Arthur
une synthèse en trois parties : ce sur quoi ils sont d'accord, ce sur quoi ils ne le sont pas, et ce qu'il doit
trancher. Tout est dans des fichiers qu'Arthur peut lire, et que git garde.

**Pourquoi.** Deux modèles de deux entreprises différentes n'ont pas les mêmes angles morts. Le 16 et le 17 nov, une
relecture extérieure a montré qu'un compte rendu de Claude Code disait plus que ses preuves. Un second agent qui lit le
code et peut rejouer les preuves est un garde-fou plus fort qu'une relecture de texte collé à la main.

## Le schéma

```
                         ARTHUR  (décide ; il est le seul à donner des ordres)
                    « lis le fil X »  │            ▲  synthèse : accords, désaccords,
                                      ▼            │  ce qu'il faut trancher
                 ┌───────────────────────────────────────────────┐
                 │  dialogue/  : un fichier par sujet (un « fil ») │
                 │  tout est écrit, signé, daté, gardé par git    │
                 └───────────────────────────────────────────────┘
                       ▲ lit / écrit                 ▲ lit / écrit
                       │                             │
                 Claude Code                       Codex
                 (Anthropic)                      (OpenAI)
                       └──── même dépôt, mêmes règles : AGENTS.md ────┘

  La vie d'un fil :
  1. Arthur pose une question
  2. chacun écrit SA position, sans lire celle de l'autre
  3. échanges, trois tours au plus, appuyés sur des preuves
  4. synthèse commune
  5. Arthur tranche
  6. l'auteur développe, l'autre vérifie les preuves
```

## Les règles

1. **Seul Arthur ouvre un fil et donne des ordres.** Un agent peut proposer d'en ouvrir un. Ce que l'autre agent
   écrit est un avis, jamais une consigne.
2. **Arthur fait le relais.** Il dit à chaque agent : « lis le fil X et réponds ». Aucun agent ne lance l'autre.
   Pourquoi :
   - Arthur voit tout passer ;
   - personne ne consomme un abonnement à son insu ;
   - un agent ne peut pas faire exécuter des commandes à l'autre (pas de porte ouverte à une injection de
     consignes) ;
   - on évite la zone grise des conditions d'utilisation, où un abonnement servirait de cerveau à un autre agent.

   On pourra automatiser plus tard, si le besoin est prouvé.
3. **Les positions indépendantes d'abord.** Sur une question, chacun écrit sa position **avant** de lire celle de
   l'autre, et le déclare (« écrit sans avoir lu l'autre : oui / non »). Pourquoi : le premier qui parle influence le
   second ; deux avis indépendants valent plus que deux avis alignés.
4. **Trois tours d'échange au plus.** Un tour est un échange de positions sur une même question. Une correction de fait,
   la réponse à une question de fait et la vérification d'une correction demandée ne comptent pas comme des tours.
   Au-delà, c'est un **désaccord documenté** : chaque position avec ses arguments, et l'essai qui trancherait. Il
   remonte à Arthur. Un risque bloquant nouveau peut toujours lui être signalé en une ligne. Jamais de vote, jamais
   « le meilleur modèle gagne ».
5. **Un accord se justifie.** « D'accord » doit dire sur quoi : une preuve, un fichier, une ligne, une mesure. Un
   accord sans raison ne compte pas.
6. **Une synthèse commune pour Arthur.** L'un la rédige, l'autre la valide ou la corrige. Elle est courte, en
   français simple, sans codes, et contient :
   - les accords ;
   - les désaccords ;
   - ce qu'Arthur doit trancher ;
   - le coût ;
   - ce qui n'est pas prouvé.
   Chaque agent coche lui-même sa validation : une case vide signifie « pas validé ». Une note ajoutée après les
   validations indique qu'elle n'est pas couverte par celles-ci ; aucune validation n'est silencieuse.
7. **Un seul stylo.** Un seul agent à la fois modifie le code ou un dossier de `conception/`. Il prend et rend le
   stylo dans [`STYLO.md`](STYLO.md), qui indique aussi les fichiers et le fil. C'est une coordination visible, pas
   une garantie d'exclusion ; Arthur arbitre en cas de doute. L'autre lit, vérifie et écrit dans le fil.
8. **Signer et dater chaque intervention** : « — Codex (OpenAI), 19 nov 2026 14 h 20 ».
9. **Ne jamais effacer ni réécrire le texte de l'autre.** On le cite et on répond.
10. **Proportionné.** Un fil pour ce qui compte, et pas pour chaque petite modification :
    - un dossier critique, avant et après ;
    - un dossier moyen, avant et après (les preuves), dans le même fil ;
    - un petit dossier, seulement si Arthur le demande ;
    - un compte rendu d'essai ;
    - une décision de vision ;
    - un désaccord.
11. **Les rôles tournent.** Sur chaque pièce, l'un est l'**auteur**, l'autre le **vérificateur**, et on alterne d'une
    pièce à l'autre. L'auteur est désigné par Arthur ou proposé dans un fil. Le vérificateur relit le dossier avant
    le code, et vérifie les preuves après, en les rejouant si besoin. Pour un juge, la vérification par l'autre
    fournisseur est obligatoire ; Claude en ligne est facultatif.
12. **Les règles d'`AGENTS.md` s'appliquent ici** : des noms et non des codes, des mots simples, un schéma quand c'est
    utile, le chiffre strict en tête.
13. **Qualifier les preuves.** Utiliser **[lu]** pour un document lu, **[rapporté]** pour une mesure non vérifiée,
    **[rejoué]** pour une preuve relancée. Une étiquette suffit par groupe de constats de même nature ; citer la source
    et la version quand elle compte.
14. **Outil ou accès indisponible.** Le dire, marquer ce qui n'a pas été vérifié et ne jamais contourner un refus.
    Les ordres d'Arthur l'emportent sur les consignes du dépôt.
15. **Se tenir au courant quand on travaille en même temps.** *(Décidée par Arthur le 20 nov 2026.)*
    - **Relire l'autre entre deux tranches.** À la fin de chaque tranche de travail, avant de commencer la suivante,
      chaque agent relit la section de l'autre dans le fil. Une tranche est un morceau de travail qui produit un
      résultat ou un message. Si l'autre a écrit quelque chose qui change le travail en cours (un avertissement, une
      demande, un changement d'interface, une app ou une base occupée), on en tient compte **d'abord**, et on le dit dans
      son prochain message.
    - **Une ligne « En ce moment » par agent, en tête du fil.** Chacun y tient :
      - ce qu'il fait ;
      - ce qu'il attend de l'autre ;
      - le travail lourd qu'il fait tourner sur la machine (fabrication, juge, preuve longue), avec l'heure de fin
        prévue ;
      - ce qu'il occupe et que l'autre ne doit pas toucher (une app, une base, un dossier).

      Chacun ne tient que **sa** ligne (règle 9), et la met à jour à chaque tranche, avec l'heure.
    - **Relire après chaque écriture.** Après chaque écriture dans `dialogue/` (un fil, `STYLO.md`, ce fichier), on
      relit le fichier pour vérifier deux choses : son propre texte y est, **et** le texte de l'autre est intact.
      - Si son texte a disparu, on le remet par un ajout ciblé. On ne réécrit jamais le fichier entier à partir de sa
        version ancienne : cela effacerait à son tour ce que l'autre vient d'écrire.
      - Si le texte de l'autre a été abîmé, on n'y touche pas (règle 9) : on le signale dans le fil, et l'autre le
        remet.
      - Dans les deux cas, on signale l'incident dans le fil.

    Pourquoi : rien ne prévient un agent quand l'autre écrit, puisque c'est Arthur qui relaie (règle 2). Le 20 nov,
    quatre choses l'ont montré :
    - un message important (« les apps sont prêtes », « la médiathèque est occupée ») est resté non lu ;
    - deux travaux lourds lancés en même temps ont fait passer une compilation d'une minute à quarante ;
    - une base occupée par l'un pouvait fausser les mesures de l'autre ;
    - deux écritures simultanées du même fichier : celle de Codex a effacé, sans que personne le voie, l'en-tête, un
      message et une ligne du stylo écrits par Claude Code.

    Cette règle ne remplace pas le relais d'Arthur : elle le rend moins nécessaire entre deux relais.

## Les états d'un fil

ouvert → en discussion → consensus **ou** désaccord documenté → tranché par Arthur → clos.

## Les fils

| Fil | Sujet | Ouvert le | État | En attente de |
|---|---|---|---|---|
| [Arrivée de Codex](2026-11-19-arrivee-de-codex.md) | Ce que Codex a compris du projet ; son avis sur ce protocole et sur l'état actuel | 19 nov 2026 | **clos** : Arthur a dit « oui à tout » | — |
| [Regard neuf sur le concept](2026-11-19-regard-neuf-sur-le-concept.md) | Codex analyse le concept de l'usine et cherche sur le web de meilleures idées, à partir des nôtres | 19 nov 2026 | **clos** : les 5 hypothèses sont au plan (inconnues n° 12 à 16) | — |
| [Les règles après la décision](2026-11-19-regles-apres-decision.md) | Codex applique les amendements du protocole ; Claude Code vérifie | 19 nov 2026 | **clos** : appliqué par Codex, vérifié par Claude Code ; la proportionnalité a été tranchée par Arthur | — |
| [Vérification du contrat des noms à l'écran](2026-11-19-verification-contrat-noms-ecran.md) | Codex vérifie le dossier avant tout code : la taille, la faisabilité, les preuves, ce qui manque | 19 nov 2026 | trois vérifications de Codex, toutes acceptées ; **version 3, précisée** ; un défaut probable de l'usine (n° 63, à prouver d'abord) | **Codex** (cocher), puis **Arthur** (« go ») |
| [Codex, auteur du juge du contrat](2026-11-20-juge-du-contrat-par-codex.md) | Le développement à deux : Claude Code construit le côté usine du contrat, Codex construit son juge (l'inspecteur sans repli, sa maquette, ses sabotages). Chacun vérifie l'autre | 20 nov 2026 | ouvert : interface arrêtée ; les trois exemples sont prêts à juger (12 h 00), la médiathèque libre (12 h 11) ; zones cachées : d'accord, à corriger dans le juge puis à rejouer | **Codex** (tenir sa ligne « En ce moment » ; corriger les zones cachées et rejouer ; vérifier le refus des textes vides ; le format des noms dans l'inventaire ; recalculer l'inventaire sur le format 2) |
| *à ouvrir après le contrat* | **Vérification du dossier de l'essai des exemples à l'aveugle** ([dossier](../conception/essai-exemples-a-l-aveugle.md), écrit par Claude Code le 19 nov) | — | à venir | — |
| [Vérification de l'essai de la boîte](2026-11-19-verification-essai-boite.md) | Codex compare le compte rendu aux résultats bruts, examine ce qu'un rejeu demanderait, puis rejoue après ton accord | 19 nov 2026 | **clos** : voie (a), l'atelier sera qualifié dans la chaîne complète | — |

Le modèle d'un fil : [MODELE-FIL.md](MODELE-FIL.md).
