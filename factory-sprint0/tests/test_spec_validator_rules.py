from agents.spec_validator import _extract_key_terms, validate_spec_requirements


def test_rule_a_extracts_prisma_model_name():
    terms = _extract_key_terms("Modèle Prisma: Product { id String, price Float }")
    assert "Product" in terms


def test_rule_b_extracts_api_route_path():
    terms = _extract_key_terms("API Route: POST /api/orders")
    assert "/api/orders" in terms


def test_rule_c_extracts_page_path():
    terms = _extract_key_terms("Page: /dashboard")
    assert "/dashboard" in terms


def test_non_mappable_requirement_has_no_terms():
    terms = _extract_key_terms("Authentification Clerk robuste")
    assert terms == []


def test_validate_spec_requirements_matches_all_rules_together():
    spec = """
    ## Schéma Prisma
    model Product { id String @id }
    ## API
    POST /api/orders
    ## Pages
    /dashboard
    """
    requirements = [
        "Modèle Prisma: Product",
        "API Route: POST /api/orders",
        "Page: /dashboard",
    ]
    result = validate_spec_requirements(spec, requirements)
    assert result["status"] == "OK"
    assert result["matched_count"] == 3
    assert result["total_mappable"] == 3
