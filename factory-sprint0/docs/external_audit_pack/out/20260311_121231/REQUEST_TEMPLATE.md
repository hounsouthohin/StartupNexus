# External Reviewer Request Template

Contexte:

Tu audites un moteur de generation d'apps base sur la stack `Next.js + Clerk + Prisma`.
Tu n'as pas besoin du contexte historique du projet. Tu te bases uniquement sur les fichiers fournis.

Mission:

Verifier si la source de verite est solide et conforme aux bonnes pratiques officielles:

- stack config
- templates
- prompts
- standards
- contracts

Contraintes:

- Pas d'opinion sans source.
- Pour chaque recommandation: inclure URL de doc officielle.
- Classer chaque point en `P0`, `P1`, `P2`.
- Donner des actions concretement implementables.

Livrable:

1. `P0 Must Fix` (bloquant production)
2. `P1 Important`
3. `P2 Nice-to-have`
4. `Keep As Is`
5. `Deprecated/Remove`
6. `Final Verdict` (Ready / Conditionally Ready / Not Ready)

Critere prioritaire:

Verifier que les regles ne sont pas contradictoires entre config, templates, prompts et standards.
