import json
import shutil
from pathlib import Path

from workflows.activities.dev_test_activity import _append_guard_rule_metrics


def test_append_guard_rule_metrics_writes_jsonl(monkeypatch):
    base = Path("logs/metrics_test_guard")
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("FACTORY_LOG_DIR", str(base.resolve()))

    _append_guard_rule_metrics(
        run_id="run-123",
        dev_meta={
            "blocking_guard_id": "authorid_requires_userid_guard",
            "gate_source": "structural",
            "guard_warning_hits": {"use_client": 2},
            "guard_warning_count": 2,
        },
        run_metric={
            "build_success": False,
            "build_attempted": True,
            "root_cause_category": "semantic_violation",
        },
        stack_id="nextjs-clerk-prisma",
    )

    out = base / "metrics" / "guard_rule_events.jsonl"
    assert out.exists(), "guard_rule_events.jsonl doit être créé"
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["run_id"] == "run-123"
    assert event["blocking_guard_id"] == "authorid_requires_userid_guard"
    assert event["guard_warning_hits"]["use_client"] == 2
    assert event["precision_proxy_tp"] is True
