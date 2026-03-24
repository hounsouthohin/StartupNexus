from agents.file_supervision_loop import FileSupervisionLoop
from agents.pre_build_validator import PreBuildValidator


def _make_validator(stack_cfg=None, required_files=None, templated_names=None, supervision_loop=None):
    return PreBuildValidator(
        stack_cfg=stack_cfg or {"content_guards": [], "path_guards": []},
        required_files=required_files or ["package.json"],
        templated_names=templated_names or set(),
        supervision_loop=supervision_loop or FileSupervisionLoop(),
        scaffold_extends_paths=set(),
        stack_id="nextjs-clerk-prisma",
        guard_warning_hits={},
    )


def test_pre_build_validator_blocks_when_supervision_pending():
    loop = FileSupervisionLoop()
    loop.on_supervisor_needs_fix("app/page.tsx")
    validator = _make_validator(supervision_loop=loop)

    blocked, message, guard_id, warnings = validator.check({"package.json": "{}"})

    assert blocked is True
    assert guard_id == "supervision_pending"
    assert "SUPERVISION" in message
    assert warnings == []


def test_pre_build_validator_blocks_on_missing_blueprint_file():
    validator = _make_validator(required_files=["package.json", "app/page.tsx"])

    blocked, message, guard_id, warnings = validator.check({"package.json": "{}"})

    assert blocked is True
    assert guard_id == "blueprint"
    assert "BLUEPRINT VALIDATOR" in message
    assert warnings == []


def test_pre_build_validator_blocks_for_forbidden_paths(monkeypatch):
    validator = _make_validator(required_files=["package.json", "app/page.tsx"])
    files = {"package.json": "{}", "app/page.tsx": "ok", "pages/index.tsx": "legacy"}

    monkeypatch.setattr("agents.pre_build_validator.get_forbidden_paths", lambda _stack_id: ["pages/"])
    monkeypatch.setattr("agents.pre_build_validator.collect_forbidden_import_violations", lambda *args, **kwargs: [])

    blocked, message, guard_id, warnings = validator.check(files)

    assert blocked is True
    assert guard_id == "forbidden_paths"
    assert "FORBIDDEN PATHS GUARD" in message
    assert warnings == []


def test_pre_build_validator_warns_on_forbidden_imports(monkeypatch):
    validator = _make_validator(required_files=["package.json", "app/page.tsx"])
    files = {"package.json": "{}", "app/page.tsx": "import { useEffect } from 'react'\nexport {}"}

    monkeypatch.setattr("agents.pre_build_validator.get_forbidden_paths", lambda _stack_id: [])
    monkeypatch.setattr(
        "agents.pre_build_validator.get_forbidden_imports",
        lambda _stack_id: ["react"],
    )

    blocked, message, guard_id, warnings = validator.check(files)

    assert blocked is False
    assert guard_id == ""
    assert message == ""
    assert any("FORBIDDEN IMPORTS WARNING" in warning for warning in warnings)


def test_pre_build_validator_blocks_on_content_guard(monkeypatch):
    stack_cfg = {
        "content_guards": [
            {
                "id": "no_use_client",
                "engine": "regex",
                "mode": "block",
                "file_prefix": "app/",
                "file_extensions": [".tsx"],
                "trigger_contains": ["use client"],
                "message_lines": ["NO_USE_CLIENT", "{details}"],
            }
        ],
        "path_guards": [],
    }
    validator = _make_validator(stack_cfg=stack_cfg, required_files=["package.json", "app/page.tsx"])
    files = {
        "package.json": "{}",
        "app/page.tsx": "'use client'\nexport default function Page() { return null }",
    }

    monkeypatch.setattr("agents.pre_build_validator.get_forbidden_paths", lambda _stack_id: [])
    monkeypatch.setattr("agents.pre_build_validator.get_forbidden_imports", lambda _stack_id: [])
    monkeypatch.setattr("agents.pre_build_validator.collect_forbidden_import_violations", lambda *args, **kwargs: [])

    blocked, message, guard_id, warnings = validator.check(files)

    assert blocked is True
    assert guard_id == "no_use_client"
    assert "NO_USE_CLIENT" in message
    assert warnings == []
