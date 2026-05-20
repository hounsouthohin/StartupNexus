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
ARCHITECT_RAG_SCORE_THRESHOLD = 0.25  # Score cosinus minimum — abaissé de 0.40 (trop restrictif : retournait 0 standards sur queries naturelles)
SPEC_COVERAGE_SUCCESS_THRESHOLD = 0.8   # spec_coverage >= seuil → SUCCESS, sinon PARTIAL
SPEC_COVERAGE_PARTIAL_THRESHOLD = 0.50  # spec_coverage >= seuil → PARTIAL, sinon BUILD_FAILED (app non-fonctionnelle)
SUBPROCESS_TIMEOUT_SHORT = 30
SUBPROCESS_TIMEOUT_MEDIUM = 60
SUBPROCESS_TIMEOUT_LONG = 600

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")

