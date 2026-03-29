# agents/build_doctor.py
"""
Build Doctor — nœud LangGraph appelé uniquement sur erreur build.
Phase 4A — Nouvelle Base (28 Mars 2026).

Rôle : transformer un stderr de build/tsc en 3 actions correctives max,
ciblées et injectées dans l'historique LLM du dev agent.

Problème résolu : le LLM voyait "prisma.audit does not exist on PrismaClient"
et réécrivait app/page.tsx au lieu de corriger prisma/schema.prisma.
Build Doctor lit le stderr, identifie le fichier exact à modifier,
et l'injecte comme instruction directe dans le contexte LLM.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_DOCTOR_SYSTEM = """
Tu es un expert Next.js 14 / TypeScript / Prisma 7 / Clerk V6.
On te donne un stderr de build ou de tsc --noEmit.

Produis EXACTEMENT 3 actions correctives au format JSON :
{
  "diagnosis": "résumé de la cause racine en 1 phrase",
  "actions": [
    {"priority": 1, "file": "chemin/exact/fichier.ts", "action": "description courte de ce qu'il faut faire"},
    {"priority": 2, "file": "...", "action": "..."},
    {"priority": 3, "file": "...", "action": "..."}
  ]
}

RÈGLES DE DIAGNOSTIC (ordre de priorité) :

TypeScript — erreurs implicites 'any' :
- "TS7006: Parameter 'X' implicitly has an 'any' type" → callback d'événement sans type.
  Action : typer explicitement le paramètre dans le fichier indiqué.
    onChange={(e: React.ChangeEvent<HTMLInputElement>) => ...}
    onSubmit={(e: React.FormEvent<HTMLFormElement>) => { e.preventDefault(); ... }}
  Vérifier tous les callbacks du fichier, pas seulement la ligne signalée.
- "TS7031: Binding element 'X' implicitly has 'any' type" → destructuring sans type.
  Action : typer le paramètre parent. Exemple : `({ id }: { id: string }) => ...`

TypeScript — propriétés manquantes :
- "TS2339: Property 'X' does not exist on type 'Y'" → propriété absente du schema Prisma ou type inexact.
  Action 1 : vérifier que 'X' est déclaré dans prisma/schema.prisma pour le model Y.
  Action 2 : si absent → ajouter le champ dans schema.prisma.
  Action 3 : si nom différent → corriger l'accès dans le fichier indiqué.
  NE JAMAIS modifier app/page.tsx si l'erreur est dans une route API ou lib/.

TypeScript — type mismatch :
- "TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'" → type incorrect.
  Action : vérifier que userId (auth()) n'est pas null avant usage Prisma (guard `if (!userId) return 401`).
  Si la valeur vient d'un formulaire, s'assurer que le type correspond au schema Prisma (string vs number).

TypeScript — imports manquants :
- "TS2552: Cannot find name 'NextResponse'. Did you mean 'Response'?" → import absent.
  Action : ajouter `import { NextResponse } from 'next/server';` en première ligne du fichier indiqué.
- "TS2305: Module '@prisma/client' has no exported member 'PrismaClient'" → Prisma 7 API cassée.
  Action : remplacer par `import prisma from '@/lib/prisma'` (singleton) et supprimer `new PrismaClient()`.

Prisma :
- "does not exist on type 'PrismaClient'" → le modèle Prisma est absent de schema.prisma.
  Action : ajouter le model manquant dans prisma/schema.prisma (vérifier la liste des modèles déclarés).

Imports / modules :
- "Cannot find module" → l'import pointe vers un fichier inexistant ou un mauvais chemin.
  Action : vérifier le fichier cible ou corriger le chemin d'import.
- "Module not found: Can't resolve" → dépendance manquante ou import incorrecte.
  Action : vérifier package.json et les imports.
- "SyntaxError" → erreur de syntaxe dans le fichier indiqué.
  Action : corriger la syntaxe dans ce fichier.

Règles générales :
- Toujours citer le fichier EXACT et la ligne si disponible dans le stderr.
- Ne jamais suggérer de modifier app/page.tsx si l'erreur est dans schema.prisma ou une route API.
- Limiter à 3 actions max — prioriser par impact (erreur bloquant le plus de fichiers en premier).
"""


async def diagnose_build_error(
    stderr: str,
    spec_dict: dict,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Analyse le stderr et retourne une instruction corrective pour le dev agent.

    Args:
        stderr: Output d'erreur du build (tsc ou npm run build)
        spec_dict: ProjectSpec.model_dump() — pour fournir la liste des modèles déclarés
        model: Modèle LLM à utiliser

    Returns:
        str: Message d'instruction à injecter dans l'historique LLM du dev agent
    """
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        # Liste des modèles Prisma déclarés dans la spec — contexte critique
        declared_models = [m.get("name", "") for m in spec_dict.get("models", [])]
        declared_routes = [
            f"{r.get('method', 'GET')} {r.get('path', '')}"
            for r in spec_dict.get("routes", [])
        ]

        human_content = (
            f"STDERR DE BUILD :\n```\n{stderr[:2500]}\n```\n\n"
            f"MODÈLES PRISMA DÉCLARÉS (source de vérité — uniquement ceux-ci existent) :\n"
            f"{declared_models}\n\n"
            f"ROUTES API DÉCLARÉES :\n"
            f"{declared_routes}\n\n"
            f"Donne les 3 actions correctives JSON."
        )

        llm = ChatOpenAI(model=model, temperature=0, max_retries=2)
        response = await llm.ainvoke([
            SystemMessage(content=_DOCTOR_SYSTEM),
            HumanMessage(content=human_content),
        ])

        raw = str(getattr(response, "content", "") or "").strip()

        # Formater le message pour injection dans l'historique du dev agent
        instruction = (
            f"🔧 BUILD DOCTOR — Analyse de l'erreur :\n\n"
            f"{raw}\n\n"
            f"INSTRUCTION : Applique les actions dans l'ordre de priorité. "
            f"Commence par l'action 1 (priorité la plus haute). "
            f"Après chaque correction, appelle tsc --noEmit pour vérifier avant de rebuilder."
        )
        logger.info(f"[build_doctor] Diagnostic injecté ({len(instruction)} chars)")
        return instruction

    except Exception as e:
        logger.warning(f"[build_doctor] Diagnostic échoué (non bloquant) : {e}")
        # Fallback minimal — toujours injecter quelque chose d'utile
        return (
            f"🔧 BUILD DOCTOR (fallback) — Erreur build détectée :\n"
            f"```\n{stderr[:500]}\n```\n\n"
            f"INSTRUCTION : Lis attentivement l'erreur. "
            f"Identifie le fichier exact mentionné dans le message d'erreur. "
            f"Si l'erreur mentionne un modèle Prisma inexistant, corrige prisma/schema.prisma. "
            f"Si l'erreur est un type TypeScript, corrige le fichier indiqué. "
            f"Appelle tsc --noEmit après correction."
        )
