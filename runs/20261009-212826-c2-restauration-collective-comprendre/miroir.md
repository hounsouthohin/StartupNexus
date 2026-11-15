# Gestion restauration — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, L'utilisateur), 12 sortes de fiches, aucun circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- relier chaque profil administrateur à rôle utilisateur : pas encore possible — lien retiré
- relier chaque profil utilisateur à rôle utilisateur : pas encore possible — lien retiré

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : rôles utilisateurs, sites, stocks, achats, inventaires, recettes, coûts des repas, factures, dépenses, dossiers RH
- a son profil administrateur, créé automatiquement, qu'il peut modifier

## L'utilisateur (invité par administrateur)
- Voit tout : rôles utilisateurs, sites
- Voit tout, crée et modifie : stocks, achats, inventaires, recettes, coûts des repas, factures, dépenses, dossiers RH
- a son profil utilisateur, créé automatiquement, qu'il peut modifier

## Les informations de chaque fiche

- **Profil administrateur** : Nom (texte court) ◦ choisi par nous
- **Profil utilisateur** : Nom (texte court) ◦ choisi par nous
- **Rôle utilisateur** : Nom (texte court) ◦ choisi par nous
- **Site** : Nom (texte court) ◦ choisi par nous
- **Stock** : Nom (texte court) ◦ choisi par nous
  - relié à : site
- **Achat** : Nom (texte court) ◦ choisi par nous
  - relié à : site
- **Inventaire** : Nom (texte court) ◦ choisi par nous
  - relié à : site, stock
- **Recette** : Nom (texte court) ◦ choisi par nous
  - relié à : site
- **Coût des repas** : Nom (texte court) ◦ choisi par nous
  - relié à : site, recette
- **Facture** : Nom (texte court) ◦ choisi par nous
  - relié à : site
- **Dépense** : Nom (texte court) ◦ choisi par nous
  - relié à : site
- **Dossier rh** : Nom (texte court) ◦ choisi par nous
  - relié à : site

## Questions

- L'utilisateur verra tous les stocks, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les inventaires qu'il voit; clôture : choisit les stocks de ses inventaires
- L'utilisateur verra tous les achats, pas seulement ceux qui le concernent — d'accord ?
- L'utilisateur verra tous les inventaires, pas seulement ceux qui le concernent — d'accord ?
- L'utilisateur verra toutes les recettes, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les coûts des repas qu'il voit; clôture : choisit les recettes de ses coûts des repas
- L'utilisateur verra tous les coûts des repas, pas seulement ceux qui le concernent — d'accord ?
- L'utilisateur verra toutes les factures, pas seulement celles qui le concernent — d'accord ?
- L'utilisateur verra toutes les dépenses, pas seulement celles qui le concernent — d'accord ?
- L'utilisateur verra tous les dossiers RH, pas seulement ceux qui le concernent — d'accord ?
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : profil administrateur → « Nom » · profil utilisateur → « Nom » · rôle utilisateur → « Nom » · site → « Nom » · stock → « Nom » · achat → « Nom » · inventaire → « Nom » · recette → « Nom » · coût des repas → « Nom » · facture → « Nom » · dépense → « Nom » · dossier RH → « Nom »
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Gestion de stock / achats / inventaires avec logique métier de quantités — « gestion des stocks, achats, inventaires »
- Calcul du coût des repas — « coût des repas »
- Facturation — « facturation »
- Tableaux de bord consolidés — « tableaux de bord consolidés »
- Reporting détaillé — « reporting détaillé par site et au niveau global »
- Exports Excel/PDF — « exports Excel/PDF »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:utilisateur:Stock` = oui
- `registre_entier:utilisateur:Achat` = oui | non
- `registre_entier:utilisateur:Inventaire` = oui | non
- `registre_entier:utilisateur:Recette` = oui
- `registre_entier:utilisateur:CoutRepas` = oui | non
- `registre_entier:utilisateur:Facture` = oui | non
- `registre_entier:utilisateur:Depense` = oui | non
- `registre_entier:utilisateur:DossierRh` = oui | non
- `nom:ProfilAdministrateur:nom` = oui | <nouveau nom>  (profil administrateur → « Nom »)
- `nom:ProfilUtilisateur:nom` = oui | <nouveau nom>  (profil utilisateur → « Nom »)
- `nom:RoleUtilisateur:nom` = oui | <nouveau nom>  (rôle utilisateur → « Nom »)
- `nom:Site:nom` = oui | <nouveau nom>  (site → « Nom »)
- `nom:Stock:nom` = oui | <nouveau nom>  (stock → « Nom »)
- `nom:Achat:nom` = oui | <nouveau nom>  (achat → « Nom »)
- `nom:Inventaire:nom` = oui | <nouveau nom>  (inventaire → « Nom »)
- `nom:Recette:nom` = oui | <nouveau nom>  (recette → « Nom »)
- `nom:CoutRepas:nom` = oui | <nouveau nom>  (coût des repas → « Nom »)
- `nom:Facture:nom` = oui | <nouveau nom>  (facture → « Nom »)
- `nom:Depense:nom` = oui | <nouveau nom>  (dépense → « Nom »)
- `nom:DossierRh:nom` = oui | <nouveau nom>  (dossier RH → « Nom »)
- `accepter_proposition` = oui | non

### Pourquoi chaque droit

- administrateur / RoleUtilisateur : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « gestion des rôles utilisateurs »
- administrateur / Site : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « restauration collective multi-sites »
- administrateur / Stock : tient le registre (supprimer : seulement si le brief le dit) — « gestion des stocks »
- administrateur / Achat : tient le registre (supprimer : seulement si le brief le dit) — « achats »
- administrateur / Inventaire : tient le registre (supprimer : seulement si le brief le dit) — « inventaires »
- administrateur / Recette : tient le registre (supprimer : seulement si le brief le dit) — « recettes »
- administrateur / CoutRepas : tient le registre (supprimer : seulement si le brief le dit) — « coût des repas »
- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « facturation »
- administrateur / Depense : tient le registre (supprimer : seulement si le brief le dit) — « dépenses »
- administrateur / DossierRh : tient le registre (supprimer : seulement si le brief le dit) — « RH »
- administrateur / ProfilAdministrateur : préréglage profil : sa propre fiche, créée automatiquement — « gestion des rôles utilisateurs »
- utilisateur / RoleUtilisateur : préréglage catalogue : visible de tous les connectés — « gestion des rôles utilisateurs »
- utilisateur / Site : préréglage catalogue : visible de tous les connectés — « restauration collective multi-sites »
- utilisateur / Stock : tient le registre (supprimer : seulement si le brief le dit) — « gestion des stocks »
- utilisateur / Achat : tient le registre (supprimer : seulement si le brief le dit) — « achats »
- utilisateur / Inventaire : tient le registre (supprimer : seulement si le brief le dit) — « inventaires »
- utilisateur / Recette : tient le registre (supprimer : seulement si le brief le dit) — « recettes »
- utilisateur / CoutRepas : tient le registre (supprimer : seulement si le brief le dit) — « coût des repas »
- utilisateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « facturation »
- utilisateur / Depense : tient le registre (supprimer : seulement si le brief le dit) — « dépenses »
- utilisateur / DossierRh : tient le registre (supprimer : seulement si le brief le dit) — « RH »
- utilisateur / ProfilUtilisateur : préréglage profil : sa propre fiche, créée automatiquement — « gestion des rôles utilisateurs »

### Refus — blocs : lien:profil

- [bloc:lien:profil] ProfilAdministrateur : un profil qui désigne une autre fiche (RoleUtilisateur) arrive en N1.3 (bloc « lien depuis un profil » pas encore construit)
- [bloc:lien:profil] ProfilUtilisateur : un profil qui désigne une autre fiche (RoleUtilisateur) arrive en N1.3 (bloc « lien depuis un profil » pas encore construit) [type=value_error, input_value={'app': {'nom': 'c2-resta...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
