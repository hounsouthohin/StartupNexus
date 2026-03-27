import asyncio
from unittest.mock import AsyncMock, patch

from agents.supervision_manager import (
    _supervise_file_inline,
    run_pre_build_deterministic_checks,
)


def test_supervise_file_inline_blocks_on_tsc_eslint_errors():
    context = {
        "requirements": [],
        "plan": {},
        "files_so_far": {},
        "project_name": "p",
        "run_id": "r",
        "stack_id": "nextjs-clerk-prisma",
    }
    tsc_result = {
        "errors": [
            {
                "file": "app/page.tsx",
                "line": 4,
                "col": 12,
                "code": "TS2322",
                "message": "Type 'number' is not assignable to type 'string'.",
            }
        ],
        "success": False,
    }
    eslint_result = {
        "errors": [
            {
                "file": "app/page.tsx",
                "line": 2,
                "col": 1,
                "code": "no-unused-vars",
                "message": "'x' is assigned a value but never used.",
            }
        ],
        "success": False,
    }

    with patch(
        "agents.supervision_manager.run_tsc_check",
        new=AsyncMock(return_value=tsc_result),
    ), patch(
        "agents.supervision_manager.run_eslint_check",
        new=AsyncMock(return_value=eslint_result),
    ), patch(
        "agents.supervision_manager.run_conformity_supervisor",
        new=AsyncMock(return_value={"status": "ok", "confidence": 0.9}),
    ) as mock_conf:
        message, results = asyncio.run(
            _supervise_file_inline(
                file_path="app/page.tsx",
                file_content="export default function Page(){return null}",
                context=context,
                supervisors=["conformity"],
                conformity_scores=[],
                security_scores=[],
                architecture_scores=[],
                project_dir="C:/tmp/project",
            )
        )

    assert message is not None
    assert "ERREUR TSC/ESLINT" in message
    assert "TS2322" in message
    assert "no-unused-vars" in message
    assert results.get("deterministic", {}).get("status") == "needs_fix"
    assert results.get("deterministic", {}).get("tsc_errors_count") == 1
    assert results.get("deterministic", {}).get("eslint_errors_count") == 1
    assert results.get("deterministic", {}).get("prisma_errors_count") == 0
    mock_conf.assert_not_called()


def test_supervise_file_inline_passes_det_context_to_llm_supervisor():
    context = {
        "requirements": ["Page: /"],
        "plan": {},
        "files_so_far": {},
        "project_name": "p",
        "run_id": "r",
        "stack_id": "nextjs-clerk-prisma",
    }
    conf_result = {"status": "ok", "confidence": 0.91}

    with patch(
        "agents.supervision_manager.run_tsc_check",
        new=AsyncMock(return_value={"errors": [], "success": True}),
    ), patch(
        "agents.supervision_manager.run_eslint_check",
        new=AsyncMock(return_value={"errors": [], "success": True}),
    ), patch(
        "agents.supervision_manager.run_conformity_supervisor",
        new=AsyncMock(return_value=conf_result),
    ) as mock_conf:
        message, results = asyncio.run(
            _supervise_file_inline(
                file_path="app/page.tsx",
                file_content="export default function Page(){return null}",
                context=context,
                supervisors=["conformity"],
                conformity_scores=[],
                security_scores=[],
                architecture_scores=[],
                project_dir="C:/tmp/project",
            )
        )

    assert message is None
    assert results.get("conformity", {}).get("status") == "ok"
    assert mock_conf.await_count == 1
    _, kwargs = mock_conf.await_args
    assert kwargs.get("det_tool_result") == "[tsc+eslint] pas d'erreur"


def test_run_pre_build_deterministic_checks_blocks_on_tsc_errors():
    tsc_result = {
        "errors": [
            {
                "file": "app/admin/page.tsx",
                "line": 10,
                "col": 3,
                "code": "TS2304",
                "message": "Cannot find name 'foo'.",
            }
        ],
        "success": False,
    }
    prisma_result = {"valid": True, "errors": []}

    with patch(
        "agents.supervision_manager.run_tsc_check",
        new=AsyncMock(return_value=tsc_result),
    ), patch(
        "agents.supervision_manager.run_prisma_validate",
        new=AsyncMock(return_value=prisma_result),
    ):
        blocked, message = asyncio.run(run_pre_build_deterministic_checks("C:/tmp/project"))

    assert blocked is True
    assert "[tsc]" in message
    assert "TS2304" in message


def test_run_pre_build_deterministic_checks_blocks_on_prisma_invalid():
    with patch(
        "agents.supervision_manager.run_tsc_check",
        new=AsyncMock(return_value={"errors": [], "success": True}),
    ), patch(
        "agents.supervision_manager.run_prisma_validate",
        new=AsyncMock(return_value={"valid": False, "errors": ["invalid datasource"]}),
    ):
        blocked, message = asyncio.run(run_pre_build_deterministic_checks("C:/tmp/project"))

    assert blocked is True
    assert "[prisma validate]" in message
    assert "invalid datasource" in message


def test_run_pre_build_deterministic_checks_all_good():
    with patch(
        "agents.supervision_manager.run_tsc_check",
        new=AsyncMock(return_value={"errors": [], "success": True}),
    ), patch(
        "agents.supervision_manager.run_prisma_validate",
        new=AsyncMock(return_value={"valid": True, "errors": []}),
    ):
        blocked, message = asyncio.run(run_pre_build_deterministic_checks("C:/tmp/project"))

    assert blocked is False
    assert message == ""
