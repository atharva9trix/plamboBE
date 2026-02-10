class LLMProcessor:

    #def process_query(self, query, retrieved_documents, profile_id):
     #   return f"LLM answer for {profile_id}: {query}"

    def process_query(
            self,
            query: str,
            retrieved_documents: str,
            profile_id: str,
            conversation_context= None
    ) -> str:
        """
        Process a query with retrieved context through Ollama gemma3:1b.
        Supports follow-up questions within a single client using conversation context.

        Args:
            query: User's question
            retrieved_documents: List of (doc_text, relevance_score) tuples from vector store
            profile_id: The profile ID being queried (for logging)
            conversation_context: Optional context from previous conversation for follow-up questions

        Returns:
            If the context contains sufficient information, provide a complete explanation, not a single-sentence summary
            LLM response string

        """

        # GUARDRAIL 1: Check if context exists
        if not retrieved_documents:
            # No context available - DO NOT call LLM
            if ENABLE_NO_CONTEXT_FALLBACK:
                # This flag should always be False in production
                return self._handle_no_context(query)
            else:
                return "This question is not within the scope of the selected client. Would you like me to perform a web search for this instead?"

        # GUARDRAIL 2: Build context string with document attribution
        context_text = self._build_context_string(retrieved_documents)

        # GUARDRAIL 3: Build the prompt with explicit isolation markers and conversation context
        full_prompt = self._build_prompt(query, context_text, profile_id, conversation_context)

        # Call LLM using the common method
        answer = self._call_ollama(full_prompt, timeout=500)

        # GUARDRAIL 4: Detect if LLM says it can't find the information
        # Replace LLM-generated "not found" messages with our standardized message
        if self._is_not_found_response(answer):
            return "This question is not within the scope of the selected client. Would you like me to perform a web search for this instead?"

        return answer


    def process_web_query(self, query):
        return f"Web answer: {query}"

llm_processor = LLMProcessor()
