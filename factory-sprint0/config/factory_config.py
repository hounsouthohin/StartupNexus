import os

# --- Qdrant Configuration ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION_NAME = "factory_standards"

# --- OpenAI Configuration ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
# Add other models if needed, e.g., for generation
# GENERATION_MODEL_GPT4 = "gpt-4o"
# GENERATION_MODEL_GPT3_5 = "gpt-3.5-turbo"

# --- Agent & Tool Configuration ---
DEFAULT_VECTOR_SEARCH_LIMIT = 10  # Standards RAG retournés (architect + dev utilisent la même valeur)
ARCHITECT_RAG_SCORE_THRESHOLD = 0.40  # Score cosinus minimum — standards en dessous ignorés (architect uniquement)
SPEC_COVERAGE_SUCCESS_THRESHOLD = 0.5  # spec_coverage >= seuil → SUCCESS, sinon PARTIAL
SPEC_COVERAGE_PARTIAL_THRESHOLD = 0.25  # spec_coverage >= seuil → PARTIAL, sinon BUILD_FAILED (app non-fonctionnelle)
SUBPROCESS_TIMEOUT_SHORT = 30
SUBPROCESS_TIMEOUT_MEDIUM = 60
SUBPROCESS_TIMEOUT_LONG = 600

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")

# --- Temporal Parallel Mode ---
# Contrôle le mode de supervision utilisé par le pipeline.
# "inline"   → supervision séquentielle dans dev.py (défaut — M0)
# "asyncio"  → asyncio.gather dans dev.py, toujours 1 activité (M1)
# "workflow" → GenerationSessionWorkflow orchestre les activités en parallèle (M2)
# "signal"   → full signal-driven + continue_as_new (M3)
TEMPORAL_PARALLEL_MODE = os.getenv("TEMPORAL_PARALLEL_MODE", "inline")
