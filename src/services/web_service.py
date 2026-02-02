from src.llm.processor import llm_processor
from src.utils.response import success_response

class WebService:

    @staticmethod
    def search(payload: dict) -> dict:
        query = payload.get("query", "").strip()
        answer = llm_processor.process_web_query(query)
        return success_response(query=query, answer=answer, source="web")
