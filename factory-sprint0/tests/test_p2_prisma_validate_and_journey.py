from workflows.activities.dev_test_activity import _run_prisma_validate
from agents.core.journey_validator import validate_user_flows


def test_prisma_validate_skip_when_no_schema(monkeypatch):
    monkeypatch.setenv("PRISMA_VALIDATE_ENABLED", "1")
    monkeypatch.setenv("PRISMA_VALIDATE_ENFORCE", "1")
    violations, details = _run_prisma_validate({"app/page.tsx": "export default function Home() {}"})
    assert violations == []
    assert details["schema_path"] == ""
    assert details["ran"] is False


def test_prisma_validate_reports_missing_cli_when_enforced(monkeypatch):
    monkeypatch.setenv("PRISMA_VALIDATE_ENABLED", "1")
    monkeypatch.setenv("PRISMA_VALIDATE_ENFORCE", "1")
    monkeypatch.setattr("workflows.activities.dev_test_activity.shutil.which", lambda _: None)
    files = {
        "prisma/schema.prisma": 'datasource db { provider = "postgresql" }',
    }
    violations, details = _run_prisma_validate(files)
    assert details["schema_path"] == "prisma/schema.prisma"
    assert details["cli_found"] is False
    assert any("PRISMA_VALIDATE_UNAVAILABLE" in v for v in violations)


def test_journey_validator_keeps_deterministic_mode_by_default(monkeypatch):
    monkeypatch.delenv("JOURNEY_LLM_FALLBACK", raising=False)
    flows = ["L'utilisateur voit son dashboard → /dashboard"]
    files = {"app/dashboard/page.tsx": "export default function Dashboard() {}"}
    result = validate_user_flows(flows, files)
    assert result["user_flows_covered"] == 1
    assert result["llm_checked"] == 0
    assert result["llm_promoted"] == []


def test_journey_validator_llm_fallback_promotes_uncovered(monkeypatch):
    monkeypatch.setenv("JOURNEY_LLM_FALLBACK", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        "agents.journey_validator._llm_judge_flow_coverage",
        lambda flow, file_keys: (True, "semantic match"),
    )
    flows = ["Accès profil utilisateur"]
    files = {"app/profile/page.tsx": "export default function Profile() {}"}
    result = validate_user_flows(flows, files)
    assert result["user_flows_covered"] == 1
    assert result["llm_checked"] == 1
    assert len(result["llm_promoted"]) == 1
