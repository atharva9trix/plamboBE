from src.profiles.manager import profile_manager
from src.llm.processor import llm_processor
from src.utils.response import success_response

class QueryService:

    @staticmethod
    def process(payload: dict) -> dict:
        client_id = payload["client_id"]
        query = payload["query"]

        vector_store = profile_manager.load_profile(client_id)
        documents = vector_store.retrieve(query)

        # query: str,
        # retrieved_documents: List[Tuple[str, float]],
        # profile_id: str,
        # conversation_context: Optional[str] = None
        answer = llm_processor.process_query(
            query=query,
            retrieved_documents=documents,
            profile_id=client_id,
            conversation_context=payload["conversation_context"]
        )

        return success_response(
            client_id=client_id,
            query=query,
            answer=answer,
            context_retrieved=len(documents)
        )
