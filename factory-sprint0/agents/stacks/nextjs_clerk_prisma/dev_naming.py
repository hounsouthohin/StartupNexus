"""
agents/stacks/nextjs_clerk_prisma/dev_naming.py
────────────────────────────────────────────────
Fonctions de nommage partagées entre tous les générateurs de la stack.

Source unique — aucun générateur ne réimplémente ces transformations localement.
Conforme au GENERATOR_CONTRACT.md § 7.

Toutes les fonctions sont pures (pas de side effects, pas d'I/O).
"""
from __future__ import annotations

import re


def pascal_to_camel(name: str) -> str:
    """Post → post, BlogPost → blogPost"""
    return name[0].lower() + name[1:] if name else name


def pascal_to_kebab(name: str) -> str:
    """BlogPost → blog-post, LeaveRequest → leave-request"""
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def pascal_to_plural_camel(name: str) -> str:
    """Post → posts, Category → categories, LeaveRequest → leaveRequests"""
    return _pluralize(pascal_to_camel(name))


def pascal_to_service_var(name: str) -> str:
    """Post → postService, Category → categoryService"""
    return pascal_to_camel(name) + "Service"


def path_to_client_component(page_path: str) -> str:
    """/dashboard → DashboardClient, /categories/new → CategoriesNewClient"""
    parts = [p for p in page_path.strip("/").split("/") if p]
    cleaned = []
    for p in parts:
        p = re.sub(r"[\[\]\.]+", "", p)
        p = re.sub(r"[^a-zA-Z0-9]", " ", p).title().replace(" ", "")
        if p:
            cleaned.append(p)
    return ("".join(cleaned) or "Home") + "Client"


def path_to_page_component(page_path: str) -> str:
    """/dashboard → DashboardPage, /blog/new → BlogNewPage"""
    parts = [p for p in page_path.strip("/").split("/") if p]
    cleaned = []
    for p in parts:
        p = re.sub(r"[\[\]\.]+", "", p)
        p = re.sub(r"[^a-zA-Z0-9]", " ", p).title().replace(" ", "")
        if p:
            cleaned.append(p)
    return ("".join(cleaned) or "Home") + "Page"


def model_to_serialized_type(name: str) -> str:
    """Post → SerializedPost"""
    return f"Serialized{name}"


def _pluralize(word: str) -> str:
    """
    Pluralise un mot camelCase ou kebab-case en anglais.
    Règles par ordre de priorité :
      -y après consonne → -ies  (category→categories, company→companies)
      -s/-sh/-ch/-x/-z  → -es
      défaut             → -s
    """
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    if word.endswith(("s", "sh", "ch", "x", "z")):
        return word + "es"
    return word + "s"
