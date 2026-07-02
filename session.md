Le plan découle directement des deux diagnostics. Voici comment ils convergent.

Le principe unificateur
Tu te souviens de ce que j'ai dit sur le backend :

"Le générateur de services reçoit le schéma Prisma complet — aucune inférence, aucun cross-référencement. C'est du calcul pur."

Et ce que j'ai dit sur le frontend :

"Le frontend a besoin du même niveau de contrat explicite — les générateurs doivent calculer davantage pour que les templates aient moins à inférer."

Et ce que le diagnostic design vient d'ajouter :

"card_style, animation_level, badge_fields existent dans le spec mais la chaîne de transmission est cassée — les templates ne les reçoivent jamais."

Ces trois constats pointent vers une seule solution : créer un Page Contract calculé déterministiquement avant toute génération de template.

Le Page Contract
Aujourd'hui un template reçoit ça :


# Ce que le template reçoit maintenant
{
  "items": [...],
  "entity_name": "Article",
  "display_fields": ["title", "content", "excerpt", "published"]
}
Avec le Page Contract, il recevrait ça :


# Ce que le template devrait recevoir
{
  # ── Contrat données ──────────────────────────────────
  "service_method":   "articleService.getAllWithRelations",
  "return_fields":    ["id", "title", "slug", "published", "category.name"],
  "nav_context":      "private",
  "list_path":        "/dashboard/articles",
  "detail_path":      "/dashboard/articles/{slug}/edit",   # ← slug, PAS id
  "back_link":        "/articles",                          # ← contexte public/privé

  # ── Contrat display ──────────────────────────────────
  "display_fields_ordered": ["title", "published", "excerpt"],  # published promu
  "badge_fields":     ["published"],     # calculé depuis Boolean fields du modèle
  "textarea_fields":  ["content", "excerpt"],

  # ── Contrat design ───────────────────────────────────
  "card_style":       "flat",
  "density":          "spacious",
  "animation_level":  "enhanced",
  "list_card_layout": "hero",
  "icon":             "FileText",
}
Zéro inférence dans le template. Tout est calculé en amont par Python.

Le plan en 3 niveaux
Niveau 0 — Bugs actifs (fixes immédiats, ~45 min)

Ces 4 bugs sont déterministes à corriger maintenant, indépendamment du plan long terme :

Bug	Fix	Fichier
article.id → article.slug dans dashboard	Calculer le param depuis spec	module_detail_with_children.py ou dev_hub_generator.py
Back link → /dashboard/articles au lieu de /articles	nav_context dans module	module_detail_with_children.py
Badge absent dans /dashboard/articles	Promouvoir published avant content dans display_fields	dev_form_generator.py
badge_fields: {} vide	Calculer depuis champs Boolean du modèle	dev_graph.py (construction du design_brief)
Niveau 1 — Contrat données (sprint correctness, ~2-3h)

Créer un calculateur dev_page_contract.py qui, pour chaque page de la spec, produit :

service_method exact à appeler
return_fields que ce service retourne (y compris relations)
nav_context (public/private) → list_path, detail_path, back_link corrects
display_fields_ordered avec boolean fields promus en tête
Les templates Jinja2 consomment ces valeurs directement. Plus de cross-référencement LLM nécessaire pour les liens.

Niveau 2 — Contrat design (sprint variety, ~2-3h)

Brancher les tokens design sur les templates :

card_style → classes Tailwind conditionnelles dans les templates (flat = no shadow, elevated = shadow-md)
density → padding conditionnel (spacious = p-6, compact = p-3)
animation_level → si enhanced, templates ajoutent motion.div avec _MOTION_INSTRUCTIONS
badge_fields calculé déterministiquement → enricher a toujours quelque chose à appliquer
Enricher reprend les list pages (mais avec les contraintes structurelles, pas un skip total)
Home page LLM reçoit le DESIGN_BRIEF en contexte
Ordre de priorité recommandé

Session actuelle  →  Niveau 0 (4 bugs, ~45 min) — impact immédiat sur l'app
Prochain sprint   →  Niveau 1 (contrat données)  — élimine toute la classe de bugs navigation/lien
Sprint suivant    →  Niveau 2 (contrat design)   — variété visuelle réelle
Le Niveau 1 est la pièce maîtresse : une fois dev_page_contract.py en place, les bugs de navigation disparaissent structurellement (pas de patch par patch). Le Niveau 2 donne la vraie différenciation visuelle entre les briefs.

On commence par les 4 bugs du Niveau 0 ?