"""
workflows/activities/preview_activity.py — SCÈNE-B automatique (25 Juil 2026).

Après un build réussi : prépare l'app (base dédiée + schéma + données de démo) et lance
le serveur `next dev` détaché, puis renvoie l'URL. L'opérateur n'a plus qu'à l'ouvrir.

Gardée par PREVIEW_ENABLED (défaut OFF) : opt-in pour ne pas relancer un serveur à chaque
brief d'un batch, ni surprendre. À activer dans l'environnement du worker :
    PREVIEW_ENABLED=1
    SEED_USER_ID=<ton id Clerk>        (pour que les données te soient visibles)
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
    CLERK_SECRET_KEY=sk_test_...

Best-effort : toute erreur est loggée et NON bloquante — un preview raté ne casse jamais
un run. Le lancement + auth Clerk est le seul maillon non testable sans navigateur.

Contrat d'entrée  : project_name, build_status
Contrat de sortie : { status, url, db?, ... }
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict

from temporalio import activity

logger = logging.getLogger(__name__)

_ON = {"1", "true", "yes", "on"}


@activity.defn(name="preview_activity")
async def preview_activity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    if os.getenv("PREVIEW_ENABLED", "0").strip().lower() not in _ON:
        return {"status": "SKIPPED_DISABLED", "url": ""}

    project_name: str = input_data.get("project_name", "")
    build_status: str = str(input_data.get("build_status", ""))
    # build_status côté workflow vaut "SUCCESS"/"PARTIAL" (pas "BUILD_SUCCESS", qui est le
    # final_message interne du dev_test). On stationne dès que l'app est réellement construite.
    if build_status not in ("SUCCESS", "PARTIAL", "BUILD_SUCCESS") or not project_name:
        return {"status": "SKIPPED_BUILD", "url": "", "build_status": build_status}

    seed_user = os.getenv("SEED_USER_ID", "user_demo")
    try:
        from run.preview import prepare_preview
        # prepare_preview est bloquant (subprocess + SDK docker) → thread dédié.
        result = await asyncio.to_thread(prepare_preview, project_name, seed_user)
        activity.logger.info(f"[preview] prêt → {result.get('url')}")
        return {"status": "READY", **result}
    except Exception as e:
        activity.logger.warning(f"[preview] non bloquant : {e}")
        return {"status": "FAILED", "url": "", "error": str(e)}
