from agents.brief_parser import parse_brief, requirements_from_parsed


def test_parse_brief_french_explicit_blocks():
    brief = """
Application: Marketplace de produits artisanaux

Modèle Prisma : Product {
  id String @id @default(cuid())
  name String
  price Float
}

Modèle Prisma : Order {
  id String @id @default(cuid())
  productId String
  buyerId String
}

Pages :
- / : catalogue
- /products/[id] : détail
- /dashboard : espace vendeur

API Routes :
- GET /api/products
- POST /api/orders
"""
    parsed = parse_brief(brief)
    assert parsed["has_explicit_models"]
    assert parsed["has_explicit_pages"]
    assert parsed["has_explicit_routes"]
    assert len(parsed["data_models"]) == 2
    assert "app/page.tsx" in parsed["pages"]
    assert "app/products/[id]/page.tsx" in parsed["pages"]
    assert "app/api/products/route.ts" in parsed["api_routes"]
    assert "GET" in parsed["api_methods"]["app/api/products/route.ts"]


def test_parse_brief_english_model_and_inline_pages():
    brief = """
Application: CRM for freelancers
Prisma Model: Contact {
  id String
  email String
}
Pages: /, /dashboard, /contacts/[id]
GET /api/contacts
POST /api/contacts
"""
    parsed = parse_brief(brief)
    assert parsed["has_explicit_models"]
    assert parsed["has_explicit_pages"]
    assert parsed["has_explicit_routes"]
    assert any(m.startswith("Contact {") for m in parsed["data_models"])
    assert "app/dashboard/page.tsx" in parsed["pages"]
    assert "app/contacts/[id]/page.tsx" in parsed["pages"]
    assert parsed["api_methods"]["app/api/contacts/route.ts"] == ["GET", "POST"]


def test_parse_brief_bullets_without_colon_are_supported():
    brief = """
Pages :
* /
* /dashboard
* /reports/[id]
"""
    parsed = parse_brief(brief)
    assert parsed["has_explicit_pages"]
    assert "app/page.tsx" in parsed["pages"]
    assert "app/dashboard/page.tsx" in parsed["pages"]
    assert "app/reports/[id]/page.tsx" in parsed["pages"]


def test_parse_brief_does_not_promote_api_paths_to_pages():
    brief = """
Pages: /, /dashboard
GET /api/products
POST /api/products
"""
    parsed = parse_brief(brief)
    assert "app/page.tsx" in parsed["pages"]
    assert "app/dashboard/page.tsx" in parsed["pages"]
    assert "app/api/products/page.tsx" not in parsed["pages"]
    assert "app/api/products/route.ts" in parsed["api_routes"]


def test_requirements_from_parsed_returns_expected_formats():
    brief = """
Modèle Prisma : Product {
  id String @id @default(cuid())
  name String
  slug String @unique
}
Pages: /products/[id]
GET /api/products/[id]
"""
    parsed = parse_brief(brief)
    requirements = requirements_from_parsed(parsed)
    assert any(r.startswith("Modèle Prisma: Product {") for r in requirements)
    assert "Page: /products/[id]" in requirements
    assert "API Route: GET /api/products/[id]" in requirements
