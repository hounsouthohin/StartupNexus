from pathlib import Path

import yaml


def test_semgrep_rules_file_is_valid_yaml_and_contains_critical_rules():
    rules_path = Path("semgrep/rules/critical.yml")
    assert rules_path.exists(), "semgrep/rules/critical.yml manquant"
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and "rules" in data
    rules = data["rules"]
    assert isinstance(rules, list) and rules
    ids = {r.get("id") for r in rules if isinstance(r, dict)}
    assert "authorid-userid-null-guard-missing" in ids
    assert "app-router-hooks-require-use-client" in ids
