from agents.brief_parser import (
    _extract_description,
    build_normalized_brief_from_parsed,
    parse_brief,
    user_flows_from_parsed,
)


def test_extract_description_skips_structural_lines():
    text = """
    - /dashboard
    Modèle Prisma : Task { id String }
    Pages: /, /dashboard
    API Routes: GET /api/tasks
    Gestion de tâches collaborative pour équipe produit
    """
    desc = _extract_description(text)
    assert desc == "Gestion de tâches collaborative pour équipe produit"


def test_user_flows_from_parsed_builds_api_and_page_flows():
    brief = """
    Application: Todo manager
    Modèle Prisma : Task {
      id String
      title String
    }
    Pages: /, /tasks/[id]
    GET /api/tasks
    POST /api/tasks
    """
    parsed = parse_brief(brief)
    flows = user_flows_from_parsed(parsed)

    assert "L'utilisateur consulte → GET /api/tasks" in flows
    assert "L'utilisateur crée → POST /api/tasks" in flows
    assert "L'utilisateur visite /" in flows
    assert "L'utilisateur visite /tasks/[id]" in flows


def test_user_flows_from_parsed_fallback_when_empty():
    parsed = parse_brief("Fais une application web utile.")
    flows = user_flows_from_parsed(parsed)
    assert flows == ["L'utilisateur accède à l'application → /"]


def test_build_normalized_brief_from_parsed_contains_expected_sections():
    brief = """
    Application: Invoice app
    Modèle Prisma : Invoice {
      id String
      amount Float
    }
    Pages: /, /invoices
    GET /api/invoices
    """
    parsed = parse_brief(brief)
    normalized = build_normalized_brief_from_parsed(parsed, brief)

    assert "APPLICATION:" in normalized
    assert "MODÈLES MÉTIER" in normalized
    assert "PAGES DEMANDÉES" in normalized
    assert "ROUTES API" in normalized
    assert "/invoices" in normalized
