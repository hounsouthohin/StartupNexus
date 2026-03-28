import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.architecture_agent import run_architecture_supervisor
from agents.build_supervisor_agent import run_build_supervisor
from agents.conformity_agent import run_conformity_supervisor
from agents.dev_loop import _run_build_supervisor_inline
from agents.supervision_manager import _supervise_file_inline
from agents.dev_test_agent import _match_supervision_routing
from agents.security_agent import run_security_supervisor


class _LLMResp:
    def __init__(self, content: str):
        self.content = content


def _mock_llm_with_payload(payload: dict):
    llm_instance = MagicMock()
    llm_bound = MagicMock()
    llm_bound.ainvoke = AsyncMock(return_value=_LLMResp(json.dumps(payload)))
    llm_instance.bind.return_value = llm_bound
    return llm_instance


def test_conformity_stub_detected():
    payload = {
        "status": "needs_fix",
        "confidence": 0.85,
        "fix_instruction": {
            "file": "app/products/page.tsx",
            "problem": "Page trop stub",
            "fix": "Afficher la vraie liste produits",
            "lines_concerned": [1, 2],
        },
    }
    with patch("agents.conformity_agent.ChatOpenAI") as mock_llm_cls:
        mock_llm_cls.return_value = _mock_llm_with_payload(payload)
        result = asyncio.run(
            run_conformity_supervisor(
                file_path="app/products/page.tsx",
                file_content="export default function P(){return <div>Products</div>}",
                requirements=["Page: /products"],
                plan={"pages": ["/products"]},
            )
        )
    assert result["status"] == "needs_fix"
    assert "fix_instruction" in result


def test_conformity_complete_page_validated():
    payload = {"status": "ok", "confidence": 0.92}
    with patch("agents.conformity_agent.ChatOpenAI") as mock_llm_cls:
        mock_llm_cls.return_value = _mock_llm_with_payload(payload)
        result = asyncio.run(
            run_conformity_supervisor(
                file_path="app/products/page.tsx",
                file_content="export default async function P(){return <ul></ul>}",
                requirements=["Page: /products"],
                plan={"pages": ["/products"]},
            )
        )
    assert result["status"] == "ok"


def test_security_missing_auth_detected():
    payload = {
        "status": "needs_fix",
        "confidence": 0.9,
        "fix_instruction": {
            "file": "app/api/posts/route.ts",
            "problem": "POST sans auth()",
            "fix": "Ajouter await auth() + if (!userId) return 401",
            "lines_concerned": [2, 5],
        },
    }
    with patch("agents.security_agent.ChatOpenAI") as mock_llm_cls:
        mock_llm_cls.return_value = _mock_llm_with_payload(payload)
        result = asyncio.run(
            run_security_supervisor(
                file_path="app/api/posts/route.ts",
                file_content=(
                    "export async function POST(){\n"
                    " await prisma.post.create({data:{title:'x'}})\n"
                    "}\n"
                ),
            )
        )
    assert result["status"] == "needs_fix"
    assert result["fix_instruction"]["lines_concerned"]


def test_security_secure_handler_validated():
    payload = {"status": "ok", "confidence": 0.95}
    with patch("agents.security_agent.ChatOpenAI") as mock_llm_cls:
        mock_llm_cls.return_value = _mock_llm_with_payload(payload)
        result = asyncio.run(
            run_security_supervisor(
                file_path="app/api/posts/route.ts",
                file_content=(
                    "export async function POST(){\n"
                    " const { userId } = await auth();\n"
                    " if (!userId) return NextResponse.json({}, {status:401});\n"
                    " await prisma.post.create({data:{authorId:userId}})\n"
                    "}\n"
                ),
            )
        )
    assert result["status"] == "ok"


def test_architecture_relation_not_exploited():
    payload = {
        "status": "needs_fix",
        "confidence": 0.88,
        "fix_instruction": {
            "file": "app/orders/page.tsx",
            "problem": "Affiche productId brut",
            "fix": "Utiliser include: { product: true } et afficher order.product.name",
            "lines_concerned": [10, 12],
        },
    }
    with patch("agents.architecture_agent._load_system_prompt", return_value="ARCH PROMPT"), patch(
        "agents.architecture_agent.ChatOpenAI"
    ) as mock_llm_cls:
        mock_llm_cls.return_value = _mock_llm_with_payload(payload)
        result = asyncio.run(
            run_architecture_supervisor(
                file_path="app/orders/page.tsx",
                file_content="orders.map(o => <li>{o.productId}</li>)",
                prisma_schema="model Order { product Product @relation(fields:[productId], references:[id]) }",
                plan={"data_models": ["Order", "Product"]},
                files_so_far={"app/orders/page.tsx": "orders.map(o => <li>{o.productId}</li>)"},
            )
        )
    assert result["status"] == "needs_fix"


def test_build_supervisor_targeted_fix():
    payload = {
        "status": "needs_fix",
        "failing_file": "app/api/posts/route.ts",
        "fix_instruction": {
            "file": "app/api/posts/route.ts",
            "problem": "Type mismatch",
            "fix": "Typer params en { id: string }",
            "lines_concerned": [3],
        },
    }
    with patch("agents.build_supervisor_agent._load_system_prompt", return_value="BUILD PROMPT"), patch(
        "agents.build_supervisor_agent.ChatOpenAI"
    ) as mock_llm_cls:
        mock_llm_cls.return_value = _mock_llm_with_payload(payload)
        result = asyncio.run(
            run_build_supervisor(
                build_stderr="app/api/posts/route.ts(3,10): error TS7006: Parameter 'params' implicitly has an 'any' type.",
                combined_files={"app/api/posts/route.ts": "export async function GET(req, { params }) {}"},
            )
        )
    assert "fix_instruction" in result
    assert result["fix_instruction"]["file"]


def test_supervisors_never_raise_on_empty_inputs():
    out1 = asyncio.run(
        run_conformity_supervisor(
            file_path="",
            file_content="",
            requirements=[],
            plan={},
        )
    )
    out2 = asyncio.run(run_security_supervisor(file_path="", file_content=""))
    out3 = asyncio.run(run_architecture_supervisor(file_path="", file_content=""))
    out4 = asyncio.run(run_build_supervisor(build_stderr="", combined_files={}))
    for item in (out1, out2, out3, out4):
        assert isinstance(item, dict)
        assert item.get("status", "skipped") in {"ok", "needs_fix", "skipped"}


def test_supervision_routing_dispatch():
    routing = {
        "app/api/**/*.ts": ["conformity", "security"],
        "app/**/*.tsx": ["conformity", "architecture"],
        "**/*.test.*": [],
        "middleware.ts": [],
    }
    assert "security" in _match_supervision_routing("app/api/posts/route.ts", routing)
    assert "conformity" in _match_supervision_routing("app/products/page.tsx", routing)
    assert _match_supervision_routing("tests/post.test.ts", routing) == []
    assert _match_supervision_routing("middleware.ts", routing) == []


@pytest.mark.skip(reason="LLM supervisors supprimés Phase C — CORRECTIONS SUPERVISEURS n'est plus produit")
def test_supervise_file_inline_returns_correction_message():
    with patch("agents.supervision_manager.run_conformity_supervisor", new=AsyncMock(return_value={
        "status": "needs_fix",
        "confidence": 0.9,
        "fix_instruction": {"problem": "Stub", "fix": "Add real UI"},
    })), patch("agents.supervision_manager.run_security_supervisor", new=AsyncMock(return_value={
        "status": "ok",
        "confidence": 0.8,
    })):
        msg, results = asyncio.run(
            _supervise_file_inline(
                file_path="app/products/page.tsx",
                file_content="export default function P(){return <div>Products</div>}",
                context={
                    "requirements": ["Page: /products"],
                    "plan": {},
                    "files_so_far": {},
                    "project_name": "p",
                    "run_id": "r",
                    "stack_id": "nextjs-clerk-prisma",
                },
                supervisors=["conformity", "security"],
                conformity_scores=[],
                security_scores=[],
                architecture_scores=[],
            )
        )
    assert isinstance(results, dict)
    assert msg is not None
    assert "CORRECTIONS SUPERVISEURS OBLIGATOIRES" in msg


def test_run_build_supervisor_inline_formats_message():
    with patch("agents.dev_loop.run_build_supervisor", new=AsyncMock(return_value={
        "status": "needs_fix",
        "fix_instruction": {
            "file": "app/api/posts/route.ts",
            "problem": "TS error",
            "fix": "Type params",
            "lines_concerned": [3],
        },
    })):
        msg = asyncio.run(
            _run_build_supervisor_inline(
                build_stderr="app/api/posts/route.ts(3,10): error TS7006",
                files={"app/api/posts/route.ts": "export async function GET(req, { params }) {}"},
                run_id="r1",
                stack_id="nextjs-clerk-prisma",
            )
        )
    assert msg is not None
    assert "[BUILD SUPERVISOR]" in msg
    assert "Fix minimal" in msg
