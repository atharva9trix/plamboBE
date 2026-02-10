from src.config.settings import CLIENTS

class QueryValidator:

    @staticmethod
    def validate(payload: dict):
        if not payload:
            raise ValueError("Payload missing")

        if payload.get("client_id") not in CLIENTS:
            raise ValueError("Invalid client_id")
        print("client validated")
        if not payload.get("query", "").strip():
            raise ValueError("Query cannot be empty")
        print("query is not empty")
