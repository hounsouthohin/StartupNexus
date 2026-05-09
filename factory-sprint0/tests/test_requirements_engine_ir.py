from agents.core.requirements_engine import compute_coverage, gate_check


def _files_ok() -> dict:
    return {
        "prisma/schema.prisma": """
datasource db {
  provider = "postgresql"
}

model Post {
  id String @id
  title String
  slug String @unique
}
""",
        "app/dashboard/page.tsx": "export default function Dashboard() { return null }",
        "app/api/posts/route.ts": "export async function POST() { return Response.json({ ok: true }) }",
    }


def test_gate_check_supports_ir_dict_and_passes_when_covered():
    requirements_ir = {
        "schema": {
            "models": [
                {
                    "name": "Post",
                    "fields": [
                        {"name": "title", "type": "String"},
                        {"name": "slug", "type": "String", "is_unique": True},
                    ],
                }
            ]
        },
        "pages": [{"path": "/dashboard", "protected": True, "type": "page"}],
        "api_routes": [{"method": "POST", "path": "/api/posts", "auth": True}],
    }
    blocked, msg = gate_check(requirements_ir, _files_ok())
    assert not blocked, msg


def test_gate_check_supports_ir_dict_and_blocks_when_missing_route():
    requirements_ir = {
        "schema": {"models": [{"name": "Post", "fields": [{"name": "title"}, {"name": "slug"}]}]},
        "pages": [{"path": "/dashboard"}],
        "api_routes": [{"method": "POST", "path": "/api/posts"}],
    }
    files = _files_ok()
    files.pop("app/api/posts/route.ts")
    blocked, msg = gate_check(requirements_ir, files)
    assert blocked
    assert "Route API manquante" in msg


def test_compute_coverage_keeps_legacy_list_strings_compatibility():
    requirements_legacy = [
        "Modèle Prisma: Post avec champs title, slug unique",
        "Page: /dashboard",
        "API Route: POST /api/posts",
    ]
    cov = compute_coverage(requirements_legacy, _files_ok())
    assert cov["requirements_total"] == 3
    assert cov["requirements_met"] == 3
    assert cov["spec_coverage"] == 1.0
