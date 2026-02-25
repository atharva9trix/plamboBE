"""
Profile Manager
Central registry for all profile vector stores
"""
from src.config.settings import CLIENTS
from typing import Dict
from src.profiles.loader import VectorStoreLoader
# from config import VALID_PROFILES
#


class ProfileManager:
    """Manages all profile vector stores with lazy loading"""

    def __init__(self):
        self._stores: Dict[str, VectorStoreLoader] = {}

    def get_store(self, profile_id: str) -> VectorStoreLoader:
        if profile_id not in CLIENTS:
            raise ValueError(
                f"Invalid profile_id: '{profile_id}'. "
                f"Valid profiles are: {sorted(CLIENTS)}"
            )

        if profile_id not in self._stores:
            print(f"Loading vector store for profile: {profile_id}")
            self._stores[profile_id] = VectorStoreLoader(profile_id)

        return self._stores[profile_id]

    def load_profile(self, profile_id: str) -> VectorStoreLoader:
        return self.get_store(profile_id)

    def list_profiles(self):
        return sorted(list(CLIENTS.keys()))

    def is_valid_profile(self, profile_id: str) -> bool:
        return profile_id in CLIENTS

    def is_query_in_scope(self, profile_id: str, query: str) -> bool:
        """
        Scope validation:
        1. Keyword match against client scope
        2. OR vector store returns at least 1 document
        """

        query_lower = query.lower()

        # 1️⃣ Keyword-based scope check
        client_config = CLIENTS.get(profile_id, {})
        scope_keywords = client_config.get("scope_keywords", [])

        for keyword in scope_keywords:
            if keyword.lower() in query_lower:
                return True

        # 2️⃣ Vector presence check (semantic fallback)
        store = self.get_store(profile_id)
        docs = store.retrieve(query, top_k=1)

        return len(docs) > 0


profile_manager = ProfileManager()
