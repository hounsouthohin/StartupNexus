"""
evaluator.py — Software Agent Factory
Évalue la qualité des runs du LearnerAgent et détecte les patterns d'échecs récurrents.

Génère : logs/shadow/patterns_report.json

Métriques principales scorées :
- build_success           → 30 pts
- files_count             → 15 pts (attendu ≥ 8–12 pour un SaaS typique)
- clerk_compliant         → 20 pts
- security_standards      → 15 pts
- qa_e2e_coverage         → 10 pts
- dev_test_coverage       → 10 pts

Score total sur 100 → qualité globale du run
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

DEFAULT_LOG_PATH = os.path.join("logs", "shadow", "learner_shadow_log.json")
DEFAULT_REPORT_PATH = os.path.join("logs", "shadow", "patterns_report.json")


class EvaluatorAgent:
    def __init__(
        self,
        log_path: str = DEFAULT_LOG_PATH,
        min_recurrence: int = 3,
        min_failure_rate_for_pattern: float = 0.10,
    ):
        self.log_path = log_path
        self.min_recurrence = max(1, int(min_recurrence))
        self.min_failure_rate_for_pattern = min_failure_rate_for_pattern

    def _read_log(self) -> Dict[str, Any]:
        if not os.path.exists(self.log_path):
            return {"suggested_standards": []}
        with open(self.log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {"suggested_standards": []}

    @staticmethod
    def _parse_value(raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                return parsed if isinstance(parsed, dict) else {"raw": raw}
            except json.JSONDecodeError:
                return {"raw": raw}
        return {"raw": raw}

    def _score_run(self, event: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Calcule le score de qualité d'un run individuel (0–100)"""
        value = self._parse_value(event.get("value", {}))
        score = 0
        breakdown = {}
        metric = event.get("metric", "")

        # 1. Build success (30 pts)
        build_ok = bool(value.get("build_success", False))
        score += 30 if build_ok else 0
        breakdown["build_success"] = 30 if build_ok else 0

        # 2. Nombre de fichiers générés (15 pts)
        files = int(value.get("files_count", value.get("total_files", 0)))
        files_score = min(15, max(0, files // 2))  # 2 fichiers = 1 pt, max 15
        score += files_score
        breakdown["files_count"] = files_score

        # 3. Conformité Clerk (20 pts)
        clerk_ok = bool(value.get("clerk_compliant", False))
        score += 20 if clerk_ok else 0
        breakdown["clerk_compliant"] = 20 if clerk_ok else 0

        # 4. Standards sécurité (15 pts)
        sec_ok = bool(value.get("security_standards", False))
        score += 15 if sec_ok else 0
        breakdown["security_standards"] = 15 if sec_ok else 0

        # 5. QA E2E coverage (10 pts)
        e2e_count = int(value.get("generated_tests_count", 0))
        if metric == "qa_run" and bool(value.get("qa_e2e_coverage", False)) and e2e_count == 0:
            e2e_count = 1
        e2e_score = min(10, e2e_count)
        score += e2e_score
        breakdown["qa_e2e_coverage"] = e2e_score

        # 6. Test coverage (10 pts)
        coverage_pct = float(value.get("test_coverage_pct", 0.0))
        cov_score = min(10, int(coverage_pct // 10))
        score += cov_score
        breakdown["dev_test_coverage"] = cov_score

        return score, breakdown

    @staticmethod
    def _is_success_event(event: Dict[str, Any], value: Dict[str, Any]) -> bool:
        metric = event.get("metric", "")
        if isinstance(event.get("success"), bool):
            return bool(event.get("success"))
        if metric == "dev_test_run":
            return bool(value.get("build_success", False))
        if metric == "qa_run":
            return bool(value.get("qa_e2e_coverage", False))
        return bool(value.get("success", False))

    def _failure_signature(self, event: Dict[str, Any]) -> str:
        metric = event["metric"]
        value = self._parse_value(event["value"])
        error = str(value.get("error", "")).strip().lower()

        if error:
            first_line = error.splitlines()[0][:120]
            return f"{metric}:error:{first_line}"

        if metric == "qa_run" and int(value.get("generated_tests_count", 0)) == 0:
            return "qa_run:error:no_tests_generated"

        if metric == "dev_test_run" and int(value.get("files_count", value.get("total_files", 0))) == 0:
            return "dev_test_run:error:no_files_generated"

        if not self._is_success_event(event, value):
            return f"{metric}:error:generic_failure"

        return f"{metric}:success"  # pas un échec

    def build_report(self) -> Dict[str, Any]:
        data = self._read_log()
        events = data.get("suggested_standards", [])
        if not isinstance(events, list):
            events = []
        if not events:
            legacy_events = data.get("events", [])
            if isinstance(legacy_events, list):
                events = legacy_events

        # ── Scoring global ───────────────────────────────────────────────────
        run_scores = []
        score_breakdowns = []
        for event in events:
            if event.get("metric") in {"run_quality", "dev_test_run", "qa_run"}:
                score, breakdown = self._score_run(event)
                run_scores.append(score)
                score_breakdowns.append(breakdown)

        avg_score = round(sum(run_scores) / len(run_scores), 1) if run_scores else 0.0
        failure_rate = 1 - (avg_score / 100)

        # ── Détection patterns d'échecs ──────────────────────────────────────
        failures = []
        for event in events:
            parsed_value = self._parse_value(event.get("value", {}))
            if not self._is_success_event(event, parsed_value):
                failure_error = parsed_value.get("error")
                if not failure_error:
                    final_message = str(parsed_value.get("final_message", "")).strip()
                    if final_message:
                        failure_error = final_message[:200]
                    elif event.get("metric") == "qa_run" and int(parsed_value.get("generated_tests_count", 0)) == 0:
                        failure_error = "no_tests_generated"
                    else:
                        failure_error = "generic_failure"
                failures.append({
                    "metric": event["metric"],
                    "project": event.get("project_name", "unknown"),
                    "timestamp": event.get("timestamp"),
                    "signature": self._failure_signature(event),
                    "error": failure_error,
                })

        by_signature = defaultdict(list)
        for f in failures:
            by_signature[f["signature"]].append(f)

        patterns = []
        for idx, (sig, items) in enumerate(sorted(by_signature.items(), key=lambda x: len(x[1]), reverse=True), 1):
            count = len(items)
            if count < self.min_recurrence:
                continue

            freq = count / len(events) if events else 0
            if freq < self.min_failure_rate_for_pattern:
                continue

            metrics = Counter(i["metric"] for i in items)
            projects = sorted({i["project"] for i in items})[:5]
            errors_sample = [i["error"] for i in items if i["error"]][:3]

            recommendation = (
                "Ajouter un standard obligatoire dans factory_standards pour corriger ce pattern récurrent."
                if "error" in sig else
                "Renforcer la vérification de ce critère dans le prompt de l'agent concerné."
            )

            patterns.append({
                "pattern_id": f"P-{idx:03d}",
                "signature": sig,
                "occurrences": count,
                "failure_rate": round(freq * 100, 2),
                "metrics": dict(metrics),
                "sample_projects": projects,
                "sample_errors": errors_sample,
                "recommendation": recommendation,
                "priority": "HIGH" if count >= 5 or freq >= 0.25 else "MEDIUM",
            })

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "log_source": self.log_path,
            "total_runs": len(events),
            "avg_quality_score": avg_score,
            "global_failure_rate": round(failure_rate * 100, 2),
            "scoring_weights": {
                "build_success": 30,
                "files_count": 15,
                "clerk_compliant": 20,
                "security_standards": 15,
                "qa_e2e_coverage": 10,
                "dev_test_coverage": 10,
            },
            "patterns_detected": len(patterns),
            "patterns": sorted(patterns, key=lambda p: p["occurrences"], reverse=True),
            "min_recurrence_threshold": self.min_recurrence,
            "min_failure_rate_threshold": self.min_failure_rate_for_pattern,
        }

    def run(self, output_path: str = DEFAULT_REPORT_PATH) -> Dict[str, Any]:
        report = self.build_report()
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return report


def evaluator_agent(
    log_path: str = DEFAULT_LOG_PATH,
    output_path: str = DEFAULT_REPORT_PATH,
    min_recurrence: int = 3,
    min_failure_rate: float = 0.10,
) -> Dict[str, Any]:
    agent = EvaluatorAgent(
        log_path=log_path,
        min_recurrence=min_recurrence,
        min_failure_rate_for_pattern=min_failure_rate,
    )
    return agent.run(output_path=output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Évalue les runs du Learner et produit patterns_report.json")
    parser.add_argument("--log-path", default=DEFAULT_LOG_PATH)
    parser.add_argument("--output-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--min-recurrence", type=int, default=3)
    parser.add_argument("--min-failure-rate", type=float, default=0.10)
    args = parser.parse_args()

    report = evaluator_agent(
        log_path=args.log_path,
        output_path=args.output_path,
        min_recurrence=args.min_recurrence,
        min_failure_rate=args.min_failure_rate,
    )

    print(json.dumps({
        "report_path": args.output_path,
        "patterns_found": len(report.get("patterns", [])),
        "avg_quality_score": report.get("avg_quality_score"),
        "failure_rate_pct": report.get("global_failure_rate"),
    }, indent=2))
