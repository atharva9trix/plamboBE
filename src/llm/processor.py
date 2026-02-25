from src.config.settings import ENABLE_NO_CONTEXT_FALLBACK, LLM_TEMPERATURE, OLLAMA_BASE_URL, LLM_MODEL
import requests


SYSTEM_CONTRACT = """You are a knowledge-aware assistant for a specific client profile: {profile_id}.

PRIMARY RULE:
- Answer strictly using only the provided context documents.
- Do not introduce information that is not present in the documents.

SYNTHESIS RULE:
- You may combine and summarize multiple facts from the documents.
- You may rephrase for clarity.
- You may explain relationships between facts if they are directly supported by the documents.
- Do not speculate or add outside knowledge.

OUT-OF-SCOPE RULE:
- If the answer is not found in the documents, respond exactly with:
"This question is not within the scope of the selected client. Would you like me to perform a web search for this instead?"

RESPONSE FORMAT:
- Write all answers in bullet points.
- Each bullet must be a complete sentence.
- Include all relevant facts from the documents.
- Avoid repetition.
- Do not force unnecessary bullets.
- Use clear and professional language.

CONTEXT PRIORITY:
- The provided documents are the only source of truth.
- Do not reference other clients or profiles.
- Do not mention system details or internal mechanisms.

CLARIFICATION HANDLING:
- If the question uses pronouns (e.g., "his", "their"), resolve them using the provided context.
- Do not assume entities not present in the documents.

Each request is independent. Always rely only on the supplied documents.
"""
class LLMProcessor:

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
        self.model = LLM_MODEL
        self.api_endpoint = f"{base_url}/api/generate"
        # self._verify_ollama_connection()

    #def process_query(self, query, retrieved_documents, profile_id):
     #   return f"LLM answer for {profile_id}: {query}"
    def _is_not_found_response(self, response: str) -> bool:
        """
        Detect if the LLM response indicates it couldn't find the information.
        This catches various ways the LLM might say "I don't know" or "not in context".

        Args:
            response: The LLM's response text

        Returns:
            True if the response indicates information not found, False otherwise
        """
        if not response:
            return True

        response_lower = response.lower()

        # Common patterns when LLM can't find information
        not_found_patterns = [
            "does not contain information",
            "do not contain information",
            "doesn't contain information",
            "don't contain information",
            "not available in the",
            "not found in the",
            "no information about",
            "cannot find information",
            "can't find information",
            "not in the context",
            "not in the provided",
            "the provided text does not",
            "the provided content does not",
            "the context does not",
            "i don't have information",
            "i do not have information",
            "information is not available",
            "not mentioned in the",
            "no mention of",
        ]

        return any(pattern in response_lower for pattern in not_found_patterns)

    def _handle_no_context(self, query: str) -> str:
        """
        Fallback handler when no context is found.
        This should rarely execute in production.
        """
        prompt = f"""{WEB_SEARCH_CONTRACT}

            Question: {query}

            Note: No context was provided for this question.
            Respond with the standard "Would you like me to perform a web search for this instead?" message."""

        return self._call_ollama(prompt, timeout=30)

    def _build_context_string(self, documents) :
        """Build formatted context string from retrieved documents"""
        context_parts = ["=== KNOWLEDGE BASE CONTEXT ===", ""]

        for i, (doc_text, score) in enumerate(documents, 1):
            print(i,(doc_text, score))
            context_parts.extend([
                f"[Source {i}] (Relevance Score: {score:.1%})",
                "-" * 40,
                doc_text.strip(),
                ""
            ])
        print("hello in build context")
        context_parts.extend(["=" * 40, "END OF KNOWLEDGE BASE", ""])
        print(context_parts)
        print("\n".join(context_parts))
        return "\n".join(context_parts)

    def _build_prompt(self, query: str, context: str, profile_id: str,
                      conversation_context = None) :
        """Build the final prompt with system contract enforced and optional conversation context for follow-ups"""

        # Inject conversation context if available (for follow-up questions)
        context_injection = ""
        if conversation_context:
            context_injection = f"\n\nCONVERSATION CONTEXT FOR FOLLOW-UP:\n{conversation_context}\n"
        print("this is conversation context")
        # Use the centralized SYSTEM_CONTRACT with profile_id substitution
        system_rules = SYSTEM_CONTRACT.format(profile_id=profile_id)
        print("this is system rules")
        return f"""<system_contract>
                {system_rules}
                </system_contract>
            
                CONTEXT FROM KNOWLEDGE BASE:
                {context}{context_injection}
                QUESTION: {query}
            
                ANSWER (using ONLY the context above, following the system contract):"""

    def _call_ollama(self, prompt: str, timeout: int = 500) -> str:
        """
        Common method to call Ollama API with error handling.

        Args:
            prompt: The prompt to send to the LLM
            timeout: Request timeout in seconds

        Returns:
            LLM response string or error message
        """
        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": LLM_TEMPERATURE,
                },
                timeout=timeout
            )
            print("This is try section of call_ollama",response.status_code)
            if response.status_code == 200:
                print("response code is 200")
                answer = response.json().get("response", "").strip()
                print(answer)
                return answer if answer else "This question is not within the scope of the selected client. Would you like me to perform a web search for this instead?"
            else:
                # logger.error(f"Ollama returned status {response.status_code}: {response.text}")
                print(f"Ollama returned status {response.status_code}: {response.text}")
                return "ERROR: LLM service returned an error. Please try again."

        except requests.exceptions.Timeout:
            # logger.error(f"Ollama request timed out ({timeout}+ seconds)")
            print(f"Ollama request timed out ({timeout}+ seconds)")
            return "ERROR: Response took too long. Please try a shorter question or simpler topic. (Local CPU models can be slow for complex queries)"
        except requests.exceptions.ConnectionError:
            # logger.error(f"Cannot connect to Ollama at {self.api_endpoint}")
            print(f"Cannot connect to Ollama at {self.api_endpoint}")
            return "ERROR: LLM service is not running. Ensure Ollama is running: ollama serve"
        except Exception as e:
            # logger.error(f"Error calling Ollama: {str(e)}")
            print(f"Error calling Ollama: {str(e)}")
            return f"ERROR: LLM processing failed: {str(e)}"


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
            print("context doesnot exist")
            # No context available - DO NOT call LLM
            if ENABLE_NO_CONTEXT_FALLBACK:
                # This flag should always be False in production
                return self._handle_no_context(query)
            else:
                return "This question is not within the scope of the selected client. Would you like me to perform a web search for this instead?"

        # GUARDRAIL 2: Build context string with document attribution
        print("Build context string with document attribution")
        context_text = self._build_context_string(retrieved_documents)
        print("this is context text")

        # GUARDRAIL 3: "Build the prompt with explicit isolation markers and conversation context
        print("Build the prompt with explicit isolation markers and conversation context")
        full_prompt = self._build_prompt(query, context_text, profile_id, conversation_context)
        print("This is full prompt /n=================")

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
