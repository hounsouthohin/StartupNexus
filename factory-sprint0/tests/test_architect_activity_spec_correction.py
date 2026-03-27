import asyncio
from unittest.mock import patch

import pytest
from temporalio.exceptions import ApplicationError

from workflows.activities.architect_activity import architect_activity


class _FakeArchitectAgent:
    def __init__(self, outputs):
        self._outputs = list(outputs)
        self.calls = 0

    async def ainvoke(self, _state):
        idx = self.calls
        self.calls += 1
        if idx >= len(self._outputs):
            idx = len(self._outputs) - 1
        return {"architect_output": self._outputs[idx]}


def _base_input():
    return {
        "phrase": "Crée une app blog avec Post",
        "project_name": "p4-m1-check",
        "stack_id": "nextjs-clerk-prisma",
    }


def test_architect_activity_recovers_after_one_corrective_attempt(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    outputs = [
        {
            "specification": "spec_v1",
            "mermaid_diagram": "graph TD; A-->B;",
            "requirements": ["Modèle Prisma: Post"],
            "user_flows": [],
            "ir_schema": [],
            "ir_pages": [],
            "ir_routes": [],
            "spec_structured": {},
        },
        {
            "specification": "spec_v2 corrigée avec Post",
            "mermaid_diagram": "graph TD; A-->B;",
            "requirements": ["Modèle Prisma: Post"],
            "user_flows": [],
            "ir_schema": [],
            "ir_pages": [],
            "ir_routes": [],
            "spec_structured": {},
        },
    ]
    fake_agent = _FakeArchitectAgent(outputs)

    spec_validation_results = [
        {
            "status": "DEGRADED",
            "unmatched_requirements": ["Modèle Prisma: Post"],
            "matched_count": 0,
            "total_mappable": 1,
        },
        {
            "status": "OK",
            "unmatched_requirements": [],
            "matched_count": 1,
            "total_mappable": 1,
        },
    ]

    with patch("workflows.activities.architect_activity._wait_for_qdrant", return_value=None), patch(
        "workflows.activities.architect_activity.validate_input", return_value=None
    ), patch(
        "workflows.activities.architect_activity.validate_output", return_value=None
    ), patch(
        "workflows.activities.architect_activity._validate_clerk_compliance", return_value=[]
    ), patch(
        "agents.architect.create_architect_agent", return_value=fake_agent
    ), patch(
        "agents.spec_validator.validate_spec_requirements", side_effect=spec_validation_results
    ) as mock_sv:
        result = asyncio.run(architect_activity(_base_input(), run_id="run-1"))

    assert result["spec_validation_status"] == "OK"
    assert result["spec_unmatched_requirements"] == []
    assert fake_agent.calls == 2
    assert mock_sv.call_count == 2


def test_architect_activity_raises_if_still_degraded_and_keeps_baseline_requirements(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    outputs = [
        {
            "specification": "spec_v1",
            "mermaid_diagram": "graph TD; A-->B;",
            "requirements": ["REQ_A"],
            "user_flows": [],
            "ir_schema": [],
            "ir_pages": [],
            "ir_routes": [],
            "spec_structured": {},
        },
        {
            # Tentative corrective qui essaye de "vider" requirements
            # pour contourner le validator.
            "specification": "spec_v2",
            "mermaid_diagram": "graph TD; A-->B;",
            "requirements": [],
            "user_flows": [],
            "ir_schema": [],
            "ir_pages": [],
            "ir_routes": [],
            "spec_structured": {},
        },
    ]
    fake_agent = _FakeArchitectAgent(outputs)
    captured_requirements = []

    def _validate(spec, requirements):
        _ = spec
        reqs = list(requirements or [])
        captured_requirements.append(reqs)
        if "REQ_A" in reqs:
            return {
                "status": "DEGRADED",
                "unmatched_requirements": ["REQ_A"],
                "matched_count": 0,
                "total_mappable": 1,
            }
        return {
            "status": "OK",
            "unmatched_requirements": [],
            "matched_count": 0,
            "total_mappable": 0,
        }

    with patch("workflows.activities.architect_activity._wait_for_qdrant", return_value=None), patch(
        "workflows.activities.architect_activity.validate_input", return_value=None
    ), patch(
        "workflows.activities.architect_activity.validate_output", return_value=None
    ), patch(
        "workflows.activities.architect_activity._validate_clerk_compliance", return_value=[]
    ), patch(
        "agents.architect.create_architect_agent", return_value=fake_agent
    ), patch(
        "agents.spec_validator.validate_spec_requirements", side_effect=_validate
    ):
        with pytest.raises(ApplicationError) as exc:
            asyncio.run(architect_activity(_base_input(), run_id="run-2"))

    assert "SPEC_DEGRADED_UNRECOVERABLE" in str(exc.value)
    assert captured_requirements == [["REQ_A"], ["REQ_A"]]
    assert fake_agent.calls == 2
