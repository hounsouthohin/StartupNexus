from pathlib import Path

import pytest


def test_todo_pilot_workflow_has_no_double_supervision():
    """
    Vérifie qu'aucune activité superviseur (conformity/security/architecture) n'est
    appelée après dev_test_activity dans le workflow.
    Source unique de supervision : supervision_manager inline dans dev.py.
    """
    # Chercher le fichier depuis la racine du repo ou depuis factory-sprint0/
    candidates = [
        Path("factory-sprint0/workflows/todo_pilot_workflow.py"),
        Path("workflows/todo_pilot_workflow.py"),
    ]
    source_path = next((p for p in candidates if p.exists()), None)
    assert source_path is not None, "todo_pilot_workflow.py introuvable"
    source = source_path.read_text(encoding="utf-8")

    # Après dev_test_activity, aucun superviseur post-build ne doit être appelé
    after_dev_test = source.split("dev_test_activity", 1)[-1]
    assert "conformity_activity" not in after_dev_test, (
        "conformity_activity trouvé après dev_test_activity — double supervision détectée"
    )
    assert "security_activity" not in after_dev_test, (
        "security_activity trouvé après dev_test_activity — double supervision détectée"
    )
    assert "architecture_activity" not in after_dev_test, (
        "architecture_activity trouvé après dev_test_activity — double supervision détectée"
    )
