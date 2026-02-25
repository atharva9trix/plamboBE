from src.config.settings import CLIENTS

class QueryValidator:

    @staticmethod
    def validate(payload: dict):
        if not payload:
            raise ValueError("Payload missing")

#        if payload.get("client_id") not in CLIENTS.lower():
#            raise ValueError("Invalid client_id")
        LOWER_CLIENTS = [key.lower() for key in CLIENTS.keys()]
        print(LOWER_CLIENTS)
        client_id = payload.get("client_id")
        print("this is clinet ", client_id)
        if not client_id or client_id.lower() not in LOWER_CLIENTS:
            raise ValueError("Invalid client_id")
        print("client validated")
        if not payload.get("query", "").strip():
            raise ValueError("Query cannot be empty")
        print("query is not empty")
