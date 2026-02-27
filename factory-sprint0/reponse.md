# Rapport d'Audit Technique - SaaS Factory

## Diagnostic de la Qualité de Production (Agent Architecte)

### 1. Faille d'Identité (Effondrement du Prompt)
- **Problème** : Le prompt système définit l'agent par son nom interne ("You are the Architect Agent") au lieu de son objectif de production.
- **Conséquence** : En l'absence d'une requête utilisateur très détaillée, l'IA génère une spécification pour "l'Architect Agent" lui-même au lieu de l'application demandée. C'est un phénomène de "miroir" où l'outil devient son propre sujet.
- **Action** : Redéfinir l'identité comme un "Expert Architecte Next.js/SaaS" focalisé exclusivement sur les besoins fonctionnels de l'utilisateur.

### 2. Contrats de Validation Laxistes
- **Problème** : Le contrat `schemas/contracts/architect_agent_contract.json` valide toute spécification dépassant 500 caractères.
- **Conséquence** : Des productions génériques, "scolaires" ou hors-sujet passent les tests de l'activité Temporal sans être bloquées. Le système accepte techniquement ce qui est sémantiquement inutile.
- **Action** : Durcir le contrat (minLength: 2500) et exiger la présence de clés sémantiques obligatoires (ex: Schéma de données, Routes API, Logique métier).

### 3. Inefficacité du RAG (Retrieval Augmented Generation)
- **Problème** : La recherche dans Qdrant est littérale, basée sur la phrase brute de l'utilisateur.
- **Conséquence** : Si l'utilisateur demande un concept métier (ex: "SaaS de logistique"), le RAG ne trouve pas de correspondance avec les standards techniques (Prisma, Clerk), laissant l'IA sans contexte technique pertinent.
- **Action** : Implémenter une étape de "Query Expansion" pour traduire les besoins métiers en termes techniques avant d'interroger la base de connaissances.

### 4. Absence de Boucle de Critique (Workflow Linéaire)
- **Problème** : Le graph LangGraph dans `agents/architect.py` est strictement linéaire (`Planner -> Spec Writer -> Diagrammer`).
- **Conséquence** : Aucune étape ne vérifie la cohérence de la sortie par rapport à l'entrée. Une erreur du Planner est amplifiée par le Spec Writer.
- **Action** : Ajouter un nœud d'Évaluation/Critique ("Self-Correction") qui compare la Spec finale à la requête initiale et demande une régénération si le score de pertinence est insuffisant.

### 5. Saturation par les Contraintes Négatives
- **Problème** : Les prompts sont saturés d'interdictions techniques (Interdit : bcrypt, JWT, NextAuth, etc.).
- **Conséquence** : La fenêtre d'attention de l'IA est accaparée par ce qu'elle NE DOIT PAS faire, au détriment de la créativité sur ce qu'elle DOIT construire.
- **Action** : Déplacer les contraintes de sécurité vers une étape de "Linter" ou de réécriture automatique, pour libérer le Spec Writer sur la conception fonctionnelle.

---
*Rapport généré par Gemini CLI - 26 Février 2026*
