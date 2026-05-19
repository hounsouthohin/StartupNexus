"""
Smoke test pour build_system_prompt() — vérifie que le template Jinja2 se rend
sans erreur et contient les sections critiques.
Ce test doit passer AVANT tout run de la factory.
"""
import pytest
from unittest.mock import MagicMock, patch


def _make_minimal_spec() -> MagicMock:
    spec = MagicMock()
    spec.models = []
    spec.pages = []
    spec.routes = []
    spec.stack_id = "nextjs-clerk-prisma"
    spec.spec_fingerprint = "smoke-test-000"
    spec.pages_detail = {}
    spec.enums = {}
    spec.to_prisma_schema_block.return_value = "// schema vide"
    spec.get_list_page_for_model.return_value = None
    return spec


def test_build_system_prompt_renders_without_error():
    """build_system_prompt() ne doit jamais lever d'exception."""
    from agents.stacks.nextjs_clerk_prisma.dev_prompts import build_system_prompt

    spec = _make_minimal_spec()
    with patch(
        "agents.stacks.nextjs_clerk_prisma.dev_prompts._build_mandatory_rag_block",
        return_value="",
    ):
        result = build_system_prompt(spec)

    assert isinstance(result, str)
    assert len(result) > 200


def test_build_system_prompt_contains_critical_sections():
    """Le prompt rendu doit contenir les blocs essentiels au comportement du LLM."""
    from agents.stacks.nextjs_clerk_prisma.dev_prompts import build_system_prompt

    spec = _make_minimal_spec()
    with patch(
        "agents.stacks.nextjs_clerk_prisma.dev_prompts._build_mandatory_rag_block",
        return_value="",
    ):
        result = build_system_prompt(spec)

    assert "OPTION A" in result
    assert "write_file" in result
    assert "SÉQUENÇAGE" in result
    assert "page-client.tsx" in result
    assert "Server Action" in result


def test_jinja2_strict_undefined_raises_on_missing_variable():
    """StrictUndefined : une variable non définie dans le template lève UndefinedError."""
    from jinja2 import Environment, StrictUndefined, UndefinedError

    env = Environment(undefined=StrictUndefined)
    with pytest.raises(UndefinedError):
        env.from_string("{{ variable_inexistante }}").render()


def test_template_file_exists_and_is_valid_jinja2():
    """Le fichier .j2 existe et se parse sans erreur Jinja2."""
    import os
    from jinja2 import Environment, StrictUndefined

    tpl_path = os.path.join(
        os.path.dirname(__file__),
        "../agents/stacks/nextjs_clerk_prisma/dev_system_prompt.j2",
    )
    assert os.path.isfile(tpl_path), f"Template introuvable : {tpl_path}"

    env = Environment(undefined=StrictUndefined)
    with open(tpl_path, encoding="utf-8") as f:
        source = f.read()

    # parse_expression lève TemplateSyntaxError si le template est mal formé
    env.parse(source)
