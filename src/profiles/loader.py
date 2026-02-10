"""
Vector Database Loader
Loads and manages FAISS vector stores for each profile
"""

import os
import pickle
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import faiss
from sentence_transformers import SentenceTransformer

from src.config.settings import PROFILES, EMBEDDING_MODEL, TOP_K_DOCUMENTS, RELEVANCE_THRESHOLD


class VectorStoreLoader:
    """Manages vector stores and retrieval for a single profile"""

    def __init__(self, profile_id: str):
        if profile_id not in PROFILES:
            raise ValueError(f"Invalid profile_id: {profile_id}. Must be one of {list(PROFILES.keys())}")

        self.profile_id = profile_id
        self.profile_config = PROFILES[profile_id]
        self.embedding_model = None
        self.index = None
        self.metadata = None
        self._load_embedder()
        self._load_vector_store()

    def _load_embedder(self):
        """Load the sentence transformer model"""
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        # print("load the sentence transformer model",EMBEDDING_MODEL)
        #


    def _load_vector_store(self):
        """Load FAISS index and metadata for the profile"""
        vector_store_path = self.profile_config["vector_store_path"]
        metadata_path = self.profile_config["metadata_path"]

        if not os.path.exists(vector_store_path):
            raise FileNotFoundError(
                f"Vector store not found for profile '{self.profile_id}' at {vector_store_path}. "
                "Run 'python -m scripts.build_indexes' first."
            )

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(
                f"Metadata not found for profile '{self.profile_id}' at {metadata_path}."
            )

        print(f"Loading vector store for profile: {self.profile_id}")
        self.index = faiss.read_index(str(vector_store_path))
        with open(metadata_path, "rb") as f:
            self.metadata = pickle.load(f)

        print(f"Vector store loaded. Contains {self.index.ntotal} documents.")

    def retrieve(self, query: str, top_k: int = TOP_K_DOCUMENTS) -> List[Tuple[str, float]]:
        """
        Retrieve top-k documents relevant to the query.

        Returns:
            List of (document_text, similarity_score) tuples, ordered by relevance
        """
        if self.index is None or self.metadata is None:
            return []

        # Encode query
        query_embedding = self.embedding_model.encode([query])

        # Search
        distances, indices = self.index.search(query_embedding, top_k)

        # Format results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for invalid results
                continue

            # Convert L2 distance to similarity score (0-1)
            similarity = 1.0 / (1.0 + float(distance))

            if similarity >= RELEVANCE_THRESHOLD:
                doc_text = self.metadata[int(idx)]
                results.append((doc_text, float(similarity)))

        return results

    def has_documents(self) -> bool:
        """Check if the vector store has any documents"""
        return self.index is not None and self.index.ntotal > 0
