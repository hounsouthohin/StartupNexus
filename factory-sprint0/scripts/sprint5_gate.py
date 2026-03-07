"""
scripts/sprint5_gate.py — Gouvernance Architect Gate (Sprint 5)

Compteur rolling sur les 5 derniers runs pour décider si le Hard Gate
Architect (spec DEGRADED → enforce) doit être activé.

Appelé depuis learner.run_learner_activity() à la fin de chaque run.
Fichier gate : logs/shadow/architect_gate.json
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_LOG_ROOT = Path(os.getenv("FACTORY_LOG_DIR", "/app/logs"))
GATE_PATH = _LOG_ROOT / "shadow" / "architect_gate.json"

_DEFAULT_GATE: dict[str, Any] = {
    "version": "1.1",
    "mode": "warn",
    "enforce": False,
    "window_size": 5,
    "thresholds": {
        "build_success_rate_min": 0.8,
        "degraded_ratio_min": 0.4,
        "panic_build_success_rate_max": 0.5,
        "panic_consecutive_runs": 3,
    },
    "counters": {
        "total_measured_runs": 0,
        "successful_runs": 0,
        "degraded_runs_count": 0,
        "consecutive_low_build_runs": 0,
    },
    "derived": {
        "rolling_build_success": 0.0,
        "rolling_degraded_ratio": 0.0,
    },
    "state": {
        "last_transition_at": None,
        "last_transition_reason": None,
    },
}


def load_gate() -> dict[str, Any]:
    """Charge le gate depuis le disque, ou retourne le défaut si absent."""
    GATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not GATE_PATH.exists():
        return json.loads(json.dumps(_DEFAULT_GATE))  # deep copy
    try:
        return json.loads(GATE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"[sprint5_gate] Impossible de lire {GATE_PATH}: {e} — reset au défaut")
        return json.loads(json.dumps(_DEFAULT_GATE))


def _save_gate(gate: dict[str, Any]) -> None:
    GATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GATE_PATH.write_text(json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8")


def update_gate(build_success: bool, spec_validation_status: str) -> dict[str, Any]:
    """
    Met à jour le gate avec les métriques du run courant.
    Applique la règle de bascule warn→enforce (et panic enforce→warn).
    Retourne le gate mis à jour.
    """
    gate = load_gate()
    now_iso = datetime.now(timezone.utc).isoformat()

    c = gate["counters"]
    d = gate["derived"]
    t = gate["thresholds"]

    # 1. Mise à jour compteurs
    c["total_measured_runs"] += 1
    if build_success:
        c["successful_runs"] += 1
        c["consecutive_low_build_runs"] = 0
    else:
        c["consecutive_low_build_runs"] += 1

    if spec_validation_status == "DEGRADED":
        c["degraded_runs_count"] += 1

    # 2. Ratios dérivés (global simple; rolling window à affiner si besoin)
    total = max(c["total_measured_runs"], 1)
    d["rolling_build_success"] = round(c["successful_runs"] / total, 3)
    d["rolling_degraded_ratio"] = round(c["degraded_runs_count"] / total, 3)

    # 3. Règles de transition
    enough_data = c["total_measured_runs"] >= gate["window_size"]

    should_enforce = (
        enough_data
        and d["rolling_build_success"] >= t["build_success_rate_min"]
        and d["rolling_degraded_ratio"] >= t["degraded_ratio_min"]
    )

    panic_disable = (
        c["consecutive_low_build_runs"] >= t["panic_consecutive_runs"]
        and d["rolling_build_success"] < t["panic_build_success_rate_max"]
    )

    if should_enforce and not gate["enforce"]:
        gate["enforce"] = True
        gate["mode"] = "enforce"
        gate["state"]["last_transition_at"] = now_iso
        gate["state"]["last_transition_reason"] = "stable-build-but-persistent-degraded-spec"
        logger.warning(
            f"[sprint5_gate] TRANSITION warn→enforce : "
            f"build_success={d['rolling_build_success']:.0%}, "
            f"degraded={d['rolling_degraded_ratio']:.0%}"
        )

    elif panic_disable and gate["enforce"]:
        gate["enforce"] = False
        gate["mode"] = "warn"
        gate["state"]["last_transition_at"] = now_iso
        gate["state"]["last_transition_reason"] = "panic-disable-low-build-success"
        logger.warning(
            f"[sprint5_gate] TRANSITION enforce→warn (panic) : "
            f"build_success={d['rolling_build_success']:.0%}, "
            f"consecutive_low={c['consecutive_low_build_runs']}"
        )

    _save_gate(gate)
    logger.info(
        f"[sprint5_gate] run #{c['total_measured_runs']} enregistré — "
        f"build={'OK' if build_success else 'FAIL'}, "
        f"spec={spec_validation_status}, "
        f"mode={gate['mode']}, "
        f"rolling_build={d['rolling_build_success']:.0%}, "
        f"degraded_ratio={d['rolling_degraded_ratio']:.0%}"
    )
    return gate
