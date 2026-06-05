"""
agents/qa.py
────────────
QA Agent — Sprint 4.8B.

Génère des tests Jest ciblés (Zod schemas + services) via OpenAI json_object.
Remplace l'ancien LangGraph par un appel direct — output garanti JSON, parsing fiable.

Focus :
  - Zod schemas  → validation pure, aucune dépendance, toujours exécutable
  - Services     → smoke test d'import + mock Prisma minimal
  - PAS de tests E2E/Playwright (Sprint 4.9)
"""
from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

_QA_MODEL = "gpt-4o"
_MAX_FILE_CHARS = 1500


def _select_target_files(generated_files: dict[str, str]) -> dict[str, str]:
    """
    Retient uniquement lib/schemas.ts et lib/services/*.service.ts.
    Ce sont les seules cibles fiables sans infrastructure E2E.
    """
    targets: dict[str, str] = {}
    for path, content in generated_files.items():
        if path == "lib/schemas.ts":
            targets[path] = content[:_MAX_FILE_CHARS]
        elif "lib/services/" in path and path.endswith(".service.ts"):
            targets[path] = content[:_MAX_FILE_CHARS]
    return targets


def _build_system_prompt() -> str:
    try:
        from utils.prompt_loader import load_prompt
        return load_prompt("qa")
    except Exception:
        return _FALLBACK_SYSTEM_PROMPT


_FALLBACK_SYSTEM_PROMPT = (
    "Tu es un générateur de tests Jest pour des apps Next.js 14 avec Prisma et Zod.\n\n"
    "MISSION : générer des tests Jest exécutables couvrant :\n"
    "1. Les schémas Zod (lib/schemas.ts) — tester cas valides ET rejets\n"
    "2. Les services Prisma (lib/services/*.service.ts) — smoke test avec mock Prisma\n\n"
    'FORMAT DE RÉPONSE : UNIQUEMENT un objet JSON valide :\n'
    '{"tests": {"chemin/fichier.test.ts": "contenu TypeScript complet"}}\n\n'
    "RÈGLES :\n"
    "- Imports depuis '@/' : import { createXxxSchema } from '@/lib/schemas'\n"
    "- Mock Prisma dans les tests service : jest.mock('@/lib/prisma', () => ({ default: { xxx: { findMany: jest.fn().mockResolvedValue([]) } } }))\n"
    "- Tests Zod : .safeParse() sur cas valide + cas invalide (champ manquant, mauvais type)\n"
    "- Tests service : vérifier que getAll(userId) retourne un tableau\n"
    "- Maximum 2 fichiers de test\n"
    "- Aucun texte hors JSON, aucun bloc markdown"
)


def _build_human_message(project_name: str, target_files: dict[str, str]) -> str:
    parts = [f"Projet : {project_name}\n"]

    if target_files:
        parts.append("## FICHIERS À TESTER\n")
        for path, content in target_files.items():
            parts.append(f"### {path}\n```typescript\n{content}\n```\n")
    else:
        parts.append("Aucun fichier cible trouvé.\n")

    parts.append(
        "\n## CONSIGNE\n"
        "Génère des tests Jest pour les schemas Zod et les services ci-dessus.\n"
        "Priorité aux schemas Zod (plus fiables, pas de mock).\n"
        'Retourne UNIQUEMENT : {"tests": {"tests/xxx.test.ts": "contenu"}}'
    )
    return "\n".join(parts)


async def generate_qa_tests(
    project_name: str,
    generated_files: dict[str, str],
    stack_id: str = "nextjs-clerk-prisma",
) -> dict[str, str]:
    """
    Génère des tests Jest via gpt-4o (json_object).
    Retourne {filepath: content} prêt à écrire sur disque.
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), max_retries=2)

    target_files = _select_target_files(generated_files)
    system_prompt = _build_system_prompt()
    human_msg = _build_human_message(project_name, target_files)

    logger.info("[qa] projet=%s fichiers_cibles=%d", project_name, len(target_files))

    try:
        response = await client.chat.completions.create(
            model=_QA_MODEL,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_msg},
            ],
        )
        raw = response.choices[0].message.content or ""
    except Exception as e:
        logger.error("[qa] LLM error: %s", e)
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("[qa] JSON parse error: %s — raw[:200]=%s", e, raw[:200])
        return {}

    tests = parsed.get("tests", {})
    if not isinstance(tests, dict):
        logger.warning("[qa] 'tests' n'est pas un dict: %s", type(tests))
        return {}

    valid = {
        path: content
        for path, content in tests.items()
        if isinstance(path, str) and isinstance(content, str) and content.strip()
    }

    logger.info("[qa] %d test(s) généré(s): %s", len(valid), list(valid.keys()))
    return valid
