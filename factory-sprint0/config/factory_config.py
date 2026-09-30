import os

# (Configuration Qdrant / embeddings retirée le 30 sept 2026 avec le RAG.)

# --- Agent & Tool Configuration ---
SPEC_COVERAGE_SUCCESS_THRESHOLD = 0.8   # spec_coverage >= seuil → SUCCESS, sinon PARTIAL
SPEC_COVERAGE_PARTIAL_THRESHOLD = 0.50  # spec_coverage >= seuil → PARTIAL, sinon BUILD_FAILED (app non-fonctionnelle)
SUBPROCESS_TIMEOUT_SHORT = 30
SUBPROCESS_TIMEOUT_MEDIUM = 60
SUBPROCESS_TIMEOUT_LONG = 600

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")

