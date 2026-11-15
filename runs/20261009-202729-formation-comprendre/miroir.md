# Gestion formation — ce que l'usine a compris

En bref : 1 rôle (Le responsable de l'organisme de formation), 10 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le responsable de l'organisme de formation (responsable de l'app)
- Voit tout, crée et modifie : entités, stagiaires, formateurs, salles, affectations à une session, factures, bilans, opérations comptables
- Voit tout, crée, modifie et supprime : tâches de rétroplanning (dans chaque session de formation)
- Sessions de formation : voit tout, en crée, les modifie, les fait passer de « convocation téléphonique » à « envoi contrat », les fait passer de « envoi contrat » à « planifier la date », les fait passer de « planifier la date » à « facturation », les fait passer de « facturation » à « établissement d'un bilan »

## Les étapes

- La session de formation passe par : « convocation téléphonique » → « envoi contrat » → « planifier la date » → « facturation » → « établissement d'un bilan »
  - Le responsable de l'organisme de formation fait passer de « convocation téléphonique » à « envoi contrat »
  - Le responsable de l'organisme de formation fait passer de « envoi contrat » à « planifier la date »
  - Le responsable de l'organisme de formation fait passer de « planifier la date » à « facturation »
  - Le responsable de l'organisme de formation fait passer de « facturation » à « établissement d'un bilan »

## Les informations de chaque fiche

- **Entité** : Nom (texte court) ◦ choisi par nous
- **Stagiaire** : Nom (texte court) ◦ choisi par nous
  - relié à : entité
- **Formateur** : Nom (texte court) ◦ choisi par nous
- **Salle** : Nom (texte court) ◦ choisi par nous
- **Session de formation** : Date (date)
  - relié à : formateur, salle
- **Affectation à une session** : Nom (texte court) ◦ choisi par nous
  - relié à : stagiaire, session de formation
- **Tâche de rétroplanning** : Intitulé (texte court)
  - relié à : dans chaque session de formation
- **Facture** : Nom (texte court) ◦ choisi par nous
- **Bilan** : Nom (texte court) ◦ choisi par nous
  - relié à : entité, session de formation
- **Opération comptable** : Nom (texte court) ◦ choisi par nous
  - relié à : facture

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : entité → « Nom » · stagiaire → « Nom » · formateur → « Nom » · salle → « Nom » · affectation à une session → « Nom » · facture → « Nom » · bilan → « Nom » · opération comptable → « Nom »

## Pas encore dans notre stock (vos mots)

- Rétroplanning / planning d'organisation des sessions — « il y a un rétroplanning d'organisation de la session »
- Convocation téléphonique — « convocation téléphonique »
- Envoi de contrats — « envoi contrat »
- Planification avec formateur et salle — « planifier la date avec le formateur et la salle »
- Facturation — « la facturation »
- Établissement d'un bilan pour l'entité de base — « l'établissement d'un bilan pour l'entité de base »
- Gestion comptable associée — « on a besoin d'une gestion comptable associée »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Entite:nom` = oui | <nouveau nom>  (entité → « Nom »)
- `nom:Stagiaire:nom` = oui | <nouveau nom>  (stagiaire → « Nom »)
- `nom:Formateur:nom` = oui | <nouveau nom>  (formateur → « Nom »)
- `nom:Salle:nom` = oui | <nouveau nom>  (salle → « Nom »)
- `nom:AffectationSession:nom` = oui | <nouveau nom>  (affectation à une session → « Nom »)
- `nom:Facture:nom` = oui | <nouveau nom>  (facture → « Nom »)
- `nom:Bilan:nom` = oui | <nouveau nom>  (bilan → « Nom »)
- `nom:OperationComptable:nom` = oui | <nouveau nom>  (opération comptable → « Nom »)

### Pourquoi chaque droit

- responsable_organisme_formation / Entite : tient le registre (supprimer : seulement si le brief le dit) — « une entité nous envoie des stagiaires »
- responsable_organisme_formation / Stagiaire : tient le registre (supprimer : seulement si le brief le dit) — « une entité nous envoie des stagiaires »
- responsable_organisme_formation / Formateur : tient le registre (supprimer : seulement si le brief le dit) — « planifier la date avec le formateur et la salle »
- responsable_organisme_formation / Salle : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « planifier la date avec le formateur et la salle »
- responsable_organisme_formation / AffectationSession : tient le registre (supprimer : seulement si le brief le dit) ; exception : « des stagiaires que nous répartissons sur des sessions de formation » — « des stagiaires que nous répartissons sur des sessions de formation » « des stagiaires que nous répartissons sur des sessions de formation »
- responsable_organisme_formation / Facture : tient le registre (supprimer : seulement si le brief le dit) — « puis la facturation »
- responsable_organisme_formation / Bilan : tient le registre (supprimer : seulement si le brief le dit) — « l'établissement d'un bilan pour l'entité de base »
- responsable_organisme_formation / OperationComptable : tient le registre (supprimer : seulement si le brief le dit) — « gestion comptable associée »
- responsable_organisme_formation / TacheRetroplanning : enfant de session de formation : même visibilité que le parent, géré par qui gère le parent — « des sessions de formation » « il y a un rétroplanning d'organisation de la session : convocation téléphonique, envoi contrat, planifier la date avec le formateur et la salle »
- responsable_organisme_formation / SessionFormation : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre — « des sessions de formation » « il y a un rétroplanning d'organisation de la session : convocation téléphonique, envoi contrat, planifier la date avec le formateur et la salle »
