import logging
from typing import List, Dict
from abc import ABC, abstractmethod

from .utils import retry_with_backoff

# Configure structured logging
logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, query: str, contexts: List[Dict]) -> str:
        """
        Generate a response based on the query and provided contexts.

        Args:
            query: The user's query
            contexts: List of context documents

        Returns:
            Generated response text
        """
        pass

class StubLLM(LLMProvider):
    """
    Stub LLM provider for development and testing.

    This provider generates simple text-based responses without requiring
    external API calls, making it useful for development and testing.
    """

    def __init__(self):
        """Initialize the stub LLM."""
        logger.debug("Initialized StubLLM")

    def generate(self, query: str, contexts: List[Dict]) -> str:
        """
        Generate a stub response based on the contexts.

        Args:
            query: The user's query
            contexts: List of context documents

        Returns:
            Simple text-based response
        """
        lines = [f"Answer (stub): Based on the following sources:"]
        for c in contexts:
            sec = c.get("section") or "Section"
            lines.append(f"- {c.get('title')} — {sec}")
        lines.append("Summary:")

        # naive summary of top contexts
        joined = " ".join([c.get("text", "") for c in contexts])
        lines.append(joined[:600] + ("..." if len(joined) > 600 else ""))

        return "\n".join(lines)

class OpenAILLM(LLMProvider):
    """
    OpenAI LLM provider with robust error handling and retry logic.

    This provider integrates with OpenAI's API for generating high-quality
    responses based on retrieved contexts.
    """

    def __init__(self, api_key: str):
        """
        Initialize the OpenAI LLM.

        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        self.client = None
        self.service_healthy = False
        self._initialize_client()
        logger.debug("Initialized OpenAILLM")

    def _initialize_client(self):
        """Initialize OpenAI client with validation."""
        try:
            from openai import OpenAI
            if not self.api_key or not self.api_key.strip():
                raise ValueError("OpenAI API key is missing or empty")

            self.client = OpenAI(api_key=self.api_key)
            # Test the API key with a minimal request
            self._validate_api_key()
            self.service_healthy = True
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            logger.error("OpenAI package not installed - using stub LLM")
            self.service_healthy = False
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.service_healthy = False

    def _validate_api_key(self):
        """Validate API key with a minimal test request."""
        try:
            # Make a minimal request to validate the API key
            self.client.models.list()
        except Exception as e:
            if "401" in str(e) or "authentication" in str(e).lower():
                raise ValueError("Invalid OpenAI API key")
            elif "429" in str(e) or "rate limit" in str(e).lower():
                logger.warning("OpenAI API rate limit reached during validation - will retry later")
            else:
                logger.warning(f"OpenAI API validation failed: {str(e)}")

    def _check_service_health(self):
        """Check service health and attempt reconnection if needed."""
        if not self.service_healthy:
            logger.info("Attempting to restore OpenAI connection...")
            self._initialize_client()
        return self.service_healthy

    def generate(self, query: str, contexts: List[Dict]) -> str:
        """
        Generate response with error handling and retry logic.

        Args:
            query: The user's query
            contexts: List of context documents

        Returns:
            Generated response text
        """
        if not self._check_service_health():
            logger.warning("OpenAI service unavailable - falling back to stub response")
            return self._generate_fallback_response(query, contexts)

        # Remove duplicates from contexts
        seen_texts = set()
        unique_contexts = []
        for c in contexts:
            text_hash = c.get('text', '')[:200]
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_contexts.append(c)

        if not unique_contexts:
            logger.warning("No valid contexts provided for generation")
            return "I don't have enough information to answer your question based on the available sources."

        def _perform_generation():
            prompt = self._build_prompt(query, unique_contexts)

            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000,  # Add max_tokens for safety
                timeout=30.0  # Add timeout
            )
            return resp.choices[0].message.content

        result = retry_with_backoff(
            _perform_generation,
            max_retries=3,
            base_delay=1.0,
            operation_name="OpenAI content generation"
        )

        if result is None:
            self.service_healthy = False
            logger.warning("OpenAI generation failed after retries - falling back to stub response")
            return self._generate_fallback_response(query, contexts)

        logger.debug("OpenAI generation completed successfully")
        return result

    def _build_prompt(self, query: str, contexts: List[Dict]) -> str:
        """
        Build the prompt for OpenAI API.

        Args:
            query: The user's query
            contexts: List of context documents

        Returns:
            Formatted prompt string
        """
        prompt = f"You are a helpful company policy assistant. Based on the provided sources, answer the question accurately and clearly. The system will automatically provide source citations, so do not include any citation formatting like 'Source:' or document references in your answer.\n\nQuestion: {query}\n\nSources:\n"
        for i, c in enumerate(contexts, 1):
            prompt += f"Source {i}: {c.get('title')} - {c.get('section', 'General')}\n{c.get('text')[:600]}\n\n"
        prompt += "Answer the question based only on the provided sources. Format lists as clear bullet points using proper Markdown format with new lines between items. Do not include any source citations or references in your answer - just provide the information."
        return prompt

    def _generate_fallback_response(self, query: str, contexts: List[Dict]) -> str:
        """
        Generate a fallback response when OpenAI is unavailable.

        Args:
            query: The user's query
            contexts: List of context documents

        Returns:
            Fallback response text
        """
        logger.info("Generating fallback response due to OpenAI service unavailability")
        return f"I apologize, but I'm currently experiencing technical difficulties with the AI service. Based on the {len(contexts)} sources available, I cannot provide a detailed answer to your question at this moment. Please try again later or contact support if the issue persists."

def create_llm_provider(provider_type: str, api_key: str = None) -> LLMProvider:
    """
    Factory function to create appropriate LLM provider instance.

    Args:
        provider_type: Type of LLM provider ("openai" or "stub")
        api_key: API key for the provider (if required)

    Returns:
        LLMProvider instance
    """
    if provider_type == "openai" and api_key:
        try:
            return OpenAILLM(api_key=api_key)
        except Exception as e:
            logger.warning(f"Failed to create OpenAI provider: {e}. Falling back to stub provider.")
            return StubLLM()
    else:
        return StubLLM()