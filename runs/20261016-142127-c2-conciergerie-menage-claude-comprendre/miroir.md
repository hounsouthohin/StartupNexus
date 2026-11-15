# Ménages Villas Victoria — ce que l'usine a compris

En bref : 2 rôles (Le gérant de la conciergerie, L'intervenant de ménage), 8 sortes de fiches, 1 circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- relier chaque Intervenant à Équipe : pas encore possible — lien retiré

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant de la conciergerie (responsable de l'app)
- Voit tout, crée et modifie : Villas, Propriétaires, Équipes, Réservations
- Voit tout, crée, modifie et supprime : Points de contrôle (dans chaque Intervention), Photos (dans chaque Intervention)
- Interventions : voit tout, en crée, les modifie, les fait passer de « réalisée (rapport de l'équipe rempli) » à « complétée par le gérant »

## L'intervenant de ménage (invité par gerant)
- Voit tout : Villas, Équipes
- Voit tout, crée et modifie : Réservations
- Voit tout, crée, modifie et supprime : Points de contrôle (dans chaque Intervention), Photos (dans chaque Intervention)
- voit les Propriétaires affichés dans les Villas qu'il consulte (sans page à part)
- a son Intervenant, créé automatiquement, qu'il peut modifier
- Interventions : voit tout, en crée, les modifie, les fait passer de « disponible » à « attribuée », les fait passer de « attribuée » à « réalisée (rapport de l'équipe rempli) »

## Les étapes

- L'intervention passe par : « disponible » → « attribuée » → « réalisée (rapport de l'équipe rempli) » → « complétée par le gérant »
  - Le gérant de la conciergerie fait passer de « réalisée (rapport de l'équipe rempli) » à « complétée par le gérant »
  - L'intervenant de ménage fait passer de « disponible » à « attribuée »
  - L'intervenant de ménage fait passer de « attribuée » à « réalisée (rapport de l'équipe rempli) »

## Les informations de chaque fiche

- **Villa** : Nom de la villa (texte court) ◦ choisi par nous
  - relié à : Propriétaire
  - proposé (à cocher) : ☐ Adresse (texte long) · ☐ Nombre de chambres (nombre)
- **Propriétaire** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Équipe** : Nom de l'équipe (texte court) · Couleur sur le planning (texte court)
- **Intervenant** : Nom (texte court)
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone)
- **Réservation** : Date d'arrivée (date) · Date de départ (date) · Heure d'arrivée (texte court) · Heure de départ (texte court) · Nombre de voyageurs (nombre)
  - relié à : Villa
  - proposé (à cocher) : ☐ Nom du voyageur principal (texte court) · ☐ Référence de la réservation (Airbnb) (texte court)
- **Intervention** : Date de l'intervention (date, facultatif) · Heure de début (texte court, facultatif) · Heure de fin (texte court, facultatif) · Anomalies signalées (texte long, facultatif) · Commentaires (texte long, facultatif) · État du logement (accueil) (texte long, facultatif) · Remarques des voyageurs (texte long, facultatif) · Dysfonctionnements (texte long, facultatif) · Informations importantes (texte long, facultatif)
  - relié à : Réservation, Équipe
  - proposé (à cocher) : ☐ Date d'envoi du rapport au propriétaire (date)
- **Point de contrôle** : Pièce ou zone contrôlée (texte court) · Contrôlé (oui / non)
  - relié à : dans chaque Intervention
  - proposé (à cocher) : ☐ Remarque sur le point (texte court)
- **Photo** : Pièce ou point photographié (texte court) · Photo (lien du fichier) (lien web)
  - relié à : dans chaque Intervention
  - proposé (à cocher) : ☐ Légende (texte court)

## Questions

- L'intervenant de ménage verra les Propriétaires (ex. nom, coordonnées) affichés dans les Villas qu'il traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Villas qu'il voit
- L'intervenant de ménage verra toutes les Réservations, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Interventions qu'il voit; clôture : choisit les Réservations de ses Interventions
- L'intervenant de ménage verra toutes les Interventions, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : voit ce qu'il modifie
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Villa → « Nom de la villa » · Propriétaire → « Nom »
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Vue planning de type calendrier : villas en ligne, dates en colonne, réservations affichées en bandes colorées — « Le planning sera inspiré du calendrier Airbnb ... les réservations affichées sous forme de bandes colorées »
- Couleur de la réservation selon son état (couleur « Disponible ») puis selon l'équipe affectée, changée automatiquement sur le planning — « la réservation change automatiquement de couleur et prend la couleur de l'équipe concernée »
- Photos obligatoires de chaque pièce et des points stratégiques dans le rapport d'intervention — « des photos obligatoires de chaque pièce et des points stratégiques »
- Génération automatique du rapport d'intervention en PDF (travail des équipes, observations, photos) — « Le rapport est ensuite automatiquement généré en PDF »
- Transmission du rapport au propriétaire, qui n'est pas utilisateur de l'application (le moyen d'envoi n'est pas précisé) — « afin d'être transmis au propriétaire »
- Suivi en temps réel des réservations, des équipes affectées et de la qualité des prestations — « suivre en temps réel les réservations, les équipes affectées et la qualité des prestations »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `vu_via:intervenant:Proprietaire` = oui
- `registre_entier:intervenant:Reservation` = oui
- `registre_entier:intervenant:Intervention` = oui
- `nom:Villa:nom` = oui | <nouveau nom>  (Villa → « Nom de la villa »)
- `nom:Proprietaire:nom` = oui | <nouveau nom>  (Propriétaire → « Nom »)
- `accepter_proposition` = oui | non
- `garder:Villa:Adresse` = oui | non
- `garder:Villa:Nombre de chambres` = oui | non
- `garder:Proprietaire:Email` = oui | non
- `garder:Proprietaire:Téléphone` = oui | non
- `garder:Intervenant:Prénom` = oui | non
- `garder:Intervenant:Téléphone` = oui | non
- `garder:Reservation:Nom du voyageur principal` = oui | non
- `garder:Reservation:Référence de la réservation (Airbnb)` = oui | non
- `garder:Intervention:Date d'envoi du rapport au propriétaire` = oui | non
- `garder:PointControle:Remarque sur le point` = oui | non
- `garder:Photo:Légende` = oui | non

### Pourquoi chaque droit

- gerant / Villa : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « les villas en ligne »
- gerant / Proprietaire : tient le registre (supprimer : seulement si le brief le dit) — « afin d'être transmis au propriétaire »
- gerant / Equipe : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « prend la couleur de l'équipe concernée »
- gerant / Reservation : tient le registre (supprimer : seulement si le brief le dit) — « Chaque réservation indique »
- gerant / PointControle : enfant de Intervention : même visibilité que le parent, géré par qui gère le parent — « je complète le rapport avec les informations relevées lors de mon accueil des voyageurs » « À la fin du ménage, l'équipe complète un rapport » « Après le ménage, je complète le rapport »
- gerant / Photo : enfant de Intervention : même visibilité que le parent, géré par qui gère le parent — « je complète le rapport avec les informations relevées lors de mon accueil des voyageurs » « À la fin du ménage, l'équipe complète un rapport » « Après le ménage, je complète le rapport »
- gerant / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; fait l'étape depuis « realisee » ; exception : « Après le ménage, je complète le rapport » ; exception : « Après le ménage, je complète le rapport » — « je complète le rapport avec les informations relevées lors de mon accueil des voyageurs » « À la fin du ménage, l'équipe complète un rapport » « Après le ménage, je complète le rapport » « Après le ménage, je complète le rapport »
- intervenant / Villa : préréglage catalogue : visible de tous les connectés — « les villas en ligne »
- intervenant / Equipe : préréglage catalogue : visible de tous les connectés — « prend la couleur de l'équipe concernée »
- intervenant / Reservation : tient le registre (supprimer : seulement si le brief le dit) — « Chaque réservation indique »
- intervenant / PointControle : enfant de Intervention : même visibilité que le parent, géré par qui gère le parent — « je complète le rapport avec les informations relevées lors de mon accueil des voyageurs » « À la fin du ménage, l'équipe complète un rapport » « Les équipes peuvent cliquer sur "Je prends cette intervention »
- intervenant / Photo : enfant de Intervention : même visibilité que le parent, géré par qui gère le parent — « je complète le rapport avec les informations relevées lors de mon accueil des voyageurs » « À la fin du ménage, l'équipe complète un rapport » « Les équipes peuvent cliquer sur "Je prends cette intervention »
- intervenant / Proprietaire : clôture : affiché dans les Villas qu'il voit
- intervenant / Intervenant : préréglage profil : sa propre fiche, créée automatiquement — « le nom de l'intervenant ou de l'équipe »
- intervenant / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Les équipes peuvent cliquer sur "Je prends cette intervention » ; exception : « À la fin du ménage, l'équipe complète un rapport » ; exception : « À la fin du ménage, l'équipe complète un rapport » — « je complète le rapport avec les informations relevées lors de mon accueil des voyageurs » « À la fin du ménage, l'équipe complète un rapport » « Les équipes peuvent cliquer sur "Je prends cette intervention » « À la fin du ménage, l'équipe complète un rapport » « À la fin du ménage, l'équipe complète un rapport »

### Refus — blocs : lien:profil

- [bloc:lien:profil] Intervenant : un profil qui désigne une autre fiche (Equipe) arrive en N1.3 (bloc « lien depuis un profil » pas encore construit) [type=value_error, input_value={'app': {'nom': 'c2-conci...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
