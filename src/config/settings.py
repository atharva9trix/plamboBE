import os
from pathlib import Path
# API_PREFIX = "/plambo_dev"

# CLIENTS = {
#     "client_a": {"profile_path": "data/client_a"},
#     "client_b": {"profile_path": "data/client_b"}
# }

PROJECT_ROOT = Path(__file__).parent.parent

CLIENTS = {
    # "vyakhyan": {
    #     "name": "Vyakhyan",
    #     "data_dir": PROJECT_ROOT / "backend" / "data" / "vyakhyan",
    #     "vector_store_path": PROJECT_ROOT / "backend" / "vector_stores" / "vyakhyan_index.faiss",
    #     "metadata_path": PROJECT_ROOT / "backend" / "vector_stores" / "vyakhyan_metadata.pkl"
    # },

    # "navaantrix": {
    #     "name": "Navaantrix",
    #     "data_dir": PROJECT_ROOT / "backend" / "data" / "navaantrix",
    #     "vector_store_path": PROJECT_ROOT / "backend" / "vector_stores" / "navaantrix_index.faiss",
    #     "metadata_path": PROJECT_ROOT / "backend" / "vector_stores" / "navaantrix_metadata.pkl"
    # },

    "plambo": {
        "name": "Plambo",
        "data_dir": "src/data/plambo",
        "vector_store_path": "src/vector_stores/plambo_index.faiss",
        "metadata_path": "src/vector_stores/plambo_metadata.pkl"
    },

    # "client_a":{
    #     "name": "Client A",
    #     "data_dir": PROJECT_ROOT / "backend" / "data" / "client_a",
    #     "vector_store_path": PROJECT_ROOT / "backend" / "vector_stores" / "client_a_index.faiss",
    #     "metadata_path": PROJECT_ROOT / "backend" / "vector_stores" / "client_a_metadata.pkl"
    # },

    # "client_b":{
    #     "name": "Client B",
    #     "data_dir": PROJECT_ROOT / "backend" / "data" / "client_b",
    #     "vector_store_path": PROJECT_ROOT / "backend" / "vector_stores" / "client_b_index.faiss",
    #     "metadata_path": PROJECT_ROOT / "backend" / "vector_stores" / "client_b_metadata.pkl"
    # },

    "kalahari": {
        "name": "Kalahari",
        "data_dir": PROJECT_ROOT / "backend" / "data" / "kalahari",
        "vector_store_path": PROJECT_ROOT / "backend" / "vector_stores" / "kalahari_index.faiss",
        "metadata_path": PROJECT_ROOT / "backend" / "vector_stores" / "kalahari_metadata.pkl"
    },

    "sovereignsilver": {
        "name": "Sovereign Silver",
        "data_dir": PROJECT_ROOT / "backend" / "data" / "sovereignsilver",
        "vector_store_path": PROJECT_ROOT / "backend" / "vector_stores" / "sovereignsilver_index.faiss",
        "metadata_path": PROJECT_ROOT / "backend" / "vector_stores" / "sovereignsilver_metadata.pkl"
    },

    "optima": {
        "name": "Optima",
        "data_dir": PROJECT_ROOT / "backend" / "data" / "optima",
        "vector_store_path": PROJECT_ROOT / "backend" / "vector_stores" / "optima_index.faiss",
        "metadata_path": PROJECT_ROOT / "backend" / "vector_stores" / "optima_metadata.pkl"
    }
}

# Keep PROFILES as alias for backward compatibility during transition
PROFILES = CLIENTS
VALID_PROFILES = set(CLIENTS.keys())

# Vector Store Settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
VECTOR_STORE_TYPE = "FAISS"

# Query Settings
TOP_K_DOCUMENTS = 5  # Number of documents to retrieve per query
RELEVANCE_THRESHOLD = 0.3  # Minimum similarity score to consider a document relevant

# LLM Settings - OLLAMA LOCAL ONLY
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = "gemma3:1b"  # CPU-friendly model (815MB, just pulled)
LLM_TEMPERATURE = 0.2  # Lower temperature for factual answers
# NOTE: Ollama doesn't use max_tokens in the same way; it generates until end-of-sequence

# Server Settings
API_HOST = "127.0.0.1"
API_PORT = 8080
API_PREFIX = "/api"

# Feature Flags
ENABLE_NO_CONTEXT_FALLBACK = False  # If True, LLM will be called even with no context
ENABLE_CROSS_PROFILE_INFERENCE = False  # Must always be False for security

# Validation
VALID_PROFILES = set(PROFILES.keys())

# LLM Configuration
LLM_CONFIG = {
    "type": "ollama",
    "model": LLM_MODEL,
    "base_url": OLLAMA_BASE_URL,
    "temperature": LLM_TEMPERATURE,
    "cpu_only": True,  # MUST be True - no GPU
}

