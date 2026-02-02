class VectorStore:
    def retrieve(self, query: str):
        return [{"content": "sample doc"}]

class ProfileManager:
    def load_profile(self, client_id: str):
        return VectorStore()

profile_manager = ProfileManager()
