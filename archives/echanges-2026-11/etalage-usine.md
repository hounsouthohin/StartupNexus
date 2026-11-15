# Notre usine à apps : nos intentions, et ce que nous attendons de ta recherche

> **À qui s'adresse ce texte** : à Claude en ligne, pour qu'il ait tout le contexte avant de faire des recherches avec nous.
> Je suis Arthur ; « nous », c'est moi et l'agent qui travaille avec moi sur le code (Claude Code).
> **Ce que c'est** : l'étalage de ce que nous voulons construire, **pas un plan d'implémentation**. Rien ici ne dit encore
> *comment* le faire, et aucune technologie n'est choisie.
> **À quoi tu nous sers** : voir le §8.

---

## 1. Nos intentions, en une phrase

Construire **notre propre usine à apps** : un système qui automatise **complètement** le développement d'apps web, de la
demande d'un client jusqu'à l'app en ligne, puis son évolution. D'abord pour les apps simples, puis **niveau après
niveau**, en apprenant à chaque fois les technologies nécessaires. L'IA y est au cœur, et nous voulons en tirer le maximum.

## 2. Ce que nous voulons, et ce que nous ne voulons pas

**Nous voulons :**
- Une usine **à nous**, entraînée par nous, **limitée au départ mais capable de s'agrandir**.
- Qu'elle **fonctionne vraiment** sur de vraies demandes, et qu'elle **montre qu'elle peut évoluer**.
- Exploiter au maximum ce que l'IA permet : agents, autonomie, systèmes intelligents, combinaisons nouvelles.
- **Chercher, innover et réfléchir ensemble** avant de construire.

**Nous ne voulons pas :**
- Vendre l'usine comme produit. C'est notre outil.
- Concurrencer les grandes plateformes de génération d'apps (Lovable, Bolt, v0…). Un agent du commerce fait peut-être la
  même chose plus vite, et ce n'est pas la question.
- Parler business pour l'instant : l'ambition commerciale est mise de côté tant que l'usine ne marche pas.
- Ouvrir l'usine librement au public.

## 3. Pour qui, et comment on y accède

- **Pour les premiers niveaux**, l'usine sert des **clients que j'accueille en personne** (sur place ou en visio). Je
  discute de leur besoin, je fournis leur demande à l'usine, et nous relisons ensemble ce qui sera construit avant la
  construction.
- **Plus tard, peut-être, un service en ligne, mais contrôlé** : accès sur invitation, jamais d'inscription libre.
- Il faudra des utilisateurs pour essayer les apps produites ; ce n'est pas un problème.

## 4. « Complètement automatisé », pour un niveau donné

Une app de ce niveau passe toute la chaîne **sans que personne ne touche au code** :

1. **Comprendre** la demande, et reconnaître son niveau et ce qu'elle exige.
2. **Faire valider** par le client ce qui sera construit.
3. **Construire** l'app entière.
4. **Prouver** qu'elle fait ce qui a été validé : droits, écrans, calculs, intégrations.
5. **Livrer** : la mettre en ligne, avec de vrais comptes, son adresse et ses sauvegardes.
6. **Faire évoluer** : appliquer une demande de changement, migrer les données, mettre à jour les technologies.
7. **Retenir** : chaque défaut et chaque leçon servent aux apps suivantes.

Un niveau n'est « appris » que lorsque toutes les apps de ce niveau passent cette chaîne. Alors seulement, on passe au
suivant.

## 5. Les niveaux d'apps web (validés par Arthur)

| Niveau | Ce que l'app fait | Exemples | Ce que l'usine doit apprendre | Où nous en sommes |
|---|---|---|---|---|
| **1. Gestion simple** | Des fiches, des rôles, qui voit et fait quoi, des étapes (états) | suivi de dossiers, interventions, congés, stock simple | données, droits, formulaires, circuits d'états | **en grande partie appris** (33 vrais briefs) ; manquent la mise en ligne et l'évolution des données |
| **2. Gestion enrichie** | Calculs, tableaux de bord, recherche et filtres, calendrier, fichiers et photos, imports et exports, e-mails | location de matériel, atelier, cabinet, salle de sport | formules, indicateurs, graphiques, stockage de fichiers, envoi d'e-mails, planning | **essayé par un agent** dans notre preuve de concept ; pas encore vérifié ni appris |
| **3. Apps connectées** | Paiements, SMS et WhatsApp, signature, cartes, synchronisation avec d'autres logiciels, plusieurs entreprises dans la même app | boutique simple, réservation avec paiement, portail client | intégrations externes, webhooks, multi-entreprises | à faire |
| **4. Temps réel et tâches de fond** | Notifications en direct, messagerie, travail à plusieurs, tâches planifiées, traitements longs | messagerie d'équipe, suivi en direct | temps réel, files de tâches, planification | à faire |
| **5. Apps intelligentes** | L'IA **dans** l'app : assistant, lecture de documents, recherche par le sens, voix, langues locales | assistant pour une PME, tri de factures | appels de modèles, recherche sémantique, voix | à faire |
| **6. Plateformes** | Plusieurs sortes d'utilisateurs qui échangent, abonnements, mobile, forte charge | place de marché, SaaS avec abonnements | facturation, montée en charge, application mobile | plus tard |

## 6. L'usine qui grandit : ce que « faire apprendre » veut dire

Pour chaque nouvelle capacité ou technologie, l'usine doit savoir :

1. **repérer** qu'une demande exige quelque chose qu'elle ne sait pas encore faire ;
2. **apprendre la technologie** : l'installer dans un environnement d'essai, la configurer, s'en servir sur des exemples ;
3. **écrire les vérifications** qui prouvent qu'elle est bien utilisée ;
4. **prouver** que ces vérifications attrapent les erreurs, en les sabotant exprès ;
5. **l'ajouter à ce qu'elle sait faire**, sans casser ce qui marchait déjà.

Aujourd'hui, c'est nous qui faisons ces cinq étapes à la main. **Une usine qui les fait elle-même, sous preuve, c'est
sans doute là qu'est l'innovation.**

## 7. D'où nous partons (en bref)

- **Ce qui existe** : une usine qui fait le niveau 1 (Next.js, ZenStack pour les règles d'accès, PostgreSQL). Elle
  comprend la demande avec des lecteurs IA, fait valider le client dans un « miroir », assemble des pièces écrites une
  fois, et vérifie chaque app avec des **juges** prouvés par sabotage : les droits rôle par rôle, et les écrans.
- **Ce que la preuve de concept d'octobre a montré** :
  - un agent de code du commerce construit une app aussi bien, et plus riche, que notre assemblage, même avec la seule
    demande ;
  - il laisse pourtant passer des erreurs de droits, que **nos juges attrapent** ;
  - avec le rapport du juge, il se corrige en une seule passe ;
  - il sait aussi migrer des données lors d'une évolution, ce que notre usine ne sait pas faire.
- **Le concept retenu à ce jour (hypothèse)** : l'usine garde la compréhension, la validation par le client, le cœur
  assemblé quand il est dans ce qu'elle sait faire, et les juges. Un agent de code fait le reste, et un **inspecteur
  indépendant** vérifie ce que l'agent écrit. Deux manques sont connus : un juge d'écrans qui marche sur n'importe quelle
  app, et la preuve par sabotage de notre juge générique.

---

## 8. Ce que nous attendons de ta recherche

Ton rôle : **réfléchir avec nous sur l'idée et chercher**, pas encore implémenter. Concrètement :

1. **Nous aider à penser l'idée**
   - les angles que nous n'avons pas vus ;
   - les combinaisons innovantes possibles (agents, juges, apprentissage, mémoire) ;
   - les points faibles de notre vision, dits franchement.
2. **L'état de l'art** : les systèmes qui ressemblent à ce que nous voulons, ce qu'ils font et ce qu'on peut en apprendre.
   En particulier :
   - les usines ou plateformes qui automatisent le développement de bout en bout ;
   - les systèmes d'agents qui **apprennent seuls** de nouveaux outils ou de nouvelles compétences ;
   - les méthodes pour vérifier automatiquement le travail d'un agent.
3. **Les technologies** : c'est pour nous la partie la plus importante. Pour chaque catégorie du §9, compare les options
   selon nos critères et dis lesquelles conviennent aux **niveaux 1 et 2 d'abord**. Signale celles qui **facilitent
   l'apprentissage par l'usine** (installer, utiliser, vérifier).
4. **La pile principale** : rester sur Next.js, ZenStack et PostgreSQL, ou changer avant le niveau 2 ? Avec les arguments
   pour et contre.
5. **« Faire apprendre » une technologie à une usine** : quelles méthodes existent, quels risques, quelles limites.

**Règles pour tes réponses** :
- cite tes sources avec leurs liens, et sépare ce qui est prouvé de ce qui est une hypothèse ;
- nomme l'exemple existant le plus proche, même s'il affaiblit l'idée ;
- reste au niveau des idées et des choix, pas du code ;
- ne parle pas de business sauf si on te le demande ;
- réponds en français.

## 9. Les technologies à choisir (catégories et premières options)

Pour chaque catégorie : ce que nous utilisons déjà, et des options **citées de mémoire, non vérifiées et non classées**.

| Catégorie | Déjà utilisé | Options à étudier |
|---|---|---|
| Langage et cadre web | Next.js + React (TypeScript) | SvelteKit, Nuxt (Vue), Remix ; côté serveur séparé : NestJS, Django, Laravel, ASP.NET Core (.NET), Rails |
| Base de données | PostgreSQL | MySQL, SQLite ; base « clé en main » : Supabase |
| Accès aux données et règles d'accès | ZenStack | Prisma, Drizzle, Entity Framework Core ; règles dans la base (RLS de PostgreSQL) ; moteurs d'autorisation : OpenFGA, Cerbos, Oso |
| Comptes et connexion | Clerk (prévu, pas branché) | Better Auth, Auth.js, Keycloak, Supabase Auth |
| Interface et design | Tailwind | shadcn/ui, systèmes de design, thèmes |
| Fichiers | — | stockage compatible S3 (MinIO, Cloudflare R2) |
| E-mails, SMS, WhatsApp | — | Resend, Postmark, Twilio, API WhatsApp Business |
| Paiement | — | Stripe, PayPal ; mobile money via des agrégateurs (pawaPay, CinetPay, PayDunya) |
| Tâches de fond et temps réel | Temporal (ancienne usine) | BullMQ, Inngest, Trigger.dev ; WebSockets |
| Mise en ligne | Docker en local | Vercel, Render, Fly.io, Railway ; un serveur loué (Hetzner, OVH) avec Coolify ; plus tard Kubernetes |
| Tests et juges | Playwright, nos juges des droits | Vitest ; tests de charge (k6) ; sécurité (OWASP ZAP, Semgrep, `npm audit`) |
| Surveillance | — | Sentry, OpenTelemetry |
| IA de l'usine | Claude Code (essais), gpt-5.5 (lecteurs) | Codex ; agents ouverts avec modèles locaux (Devstral, Qwen-Coder, GLM, DeepSeek) ; MCP pour donner des outils aux agents |
| IA dans les apps (niveau 5) | — | API de modèles, recherche par vecteurs (pgvector), voix |

**Nos critères pour choisir :**
- **Maturité et communauté** : une technologie solide, documentée, maintenue.
- **Bien connue des agents** : plus il existe d'exemples publics, mieux les agents l'écrivent.
- **Vérifiable** : nos juges doivent pouvoir prouver qu'elle est bien utilisée.
- **Indépendance** : licence libre, auto-hébergeable, pas de dépendance à un seul fournisseur.
- **Une technologie par besoin**, et peu de dépendances en tout.
- **Coût** au départ et à l'usage.
- **Une pile principale d'abord**, les autres ensuite (.NET, Laravel…).
