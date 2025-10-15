# ADR-002: LLM Provider Strategy

## Status
**Accepted**

## Context
The RAG system needs to generate answers based on retrieved document chunks. We must support both local development (offline) and production scenarios (online) while providing consistent behavior across environments.

## Decision
We will implement a dual-provider strategy with automatic fallback capabilities:

### Provider Hierarchy

1. **Primary (Production)**: OpenAI gpt-4o-mini
   - **Use Case**: Production deployments with API keys
   - **Features**: High-quality responses, advanced reasoning
   - **Configuration**: `LLM_PROVIDER=openai`, `OPENAI_API_KEY` required

2. **Secondary (Development/Backup)**: Stub LLM
   - **Use Case**: Local development, offline operation, API failures
   - **Features**: Deterministic responses, no external dependencies
   - **Configuration**: `LLM_PROVIDER=stub` (default)

### Implementation Strategy

```python
class LLMProvider:
    def __init__(self):
        self.provider = settings.llm_provider
        self.api_key = settings.openai_api_key

        if self.provider == "openai" and self.api_key:
            try:
                self.llm = OpenAILM(api_key=self.api_key)
                self.llm_name = "openai:gpt-4o-mini"
            except Exception:
                self.llm = StubLLM()
                self.llm_name = "stub"
        else:
            self.llm = StubLLM()
            self.llm_name = "stub"
```

### Fallback Mechanisms

1. **Initialization Fallback**: If OpenAI initialization fails, fall back to Stub
2. **Runtime Fallback**: If OpenAI API calls fail, provide fallback responses
3. **Manual Override**: Environment variable can force specific provider

### Prompt Adaptation

```python
def generate(self, query: str, contexts: List[Dict]) -> str:
    if isinstance(self.llm, OpenAILLM):
        prompt = self._build_openai_prompt(query, contexts)
        return self._call_openai_api(prompt)
    else:
        return self._generate_stub_response(query, contexts)
```

## Rationale

### 1. **Reliability First**
- **Benefit**: System always provides some answer, never fails completely
- **Benefit**: Graceful degradation during outages
- **Decision**: Essential for production systems

### 2. **Development Experience**
- **Benefit**: Local development works without API keys
- **Benefit**: No costs during development/testing
- **Benefit**: Deterministic behavior for testing
- **Decision**: Improves developer productivity

### 3. **Quality vs. Availability Trade-off**
- **Benefit**: OpenAI provides higher quality responses
- **Benefit**: Stub model ensures baseline functionality
- **Decision**: Balanced approach serving both needs

### 4. **Cost Management**
- **Benefit**: Local development uses no paid resources
- **Benefit**: Fallback prevents unexpected costs
- **Decision**: Budget-conscious development approach

### 5. **Configuration Flexibility**
- **Benefit**: Easy to switch providers for testing
- **Benefit**: Environment-specific configurations
- **Decision**: Supports different deployment scenarios

## Consequences

### Positive
- **High Availability**: System never completely fails
- **Development Efficiency**: No API setup required for local development
- **Cost Control**: Local development uses free resources
- **Production Quality**: OpenAI provides high-quality responses when available
- **Testing Consistency**: Stub model enables reproducible tests

### Negative
- **Response Variability**: Different providers may produce different answers
- **Configuration Complexity**: Multiple provider configurations to manage
- **Fallback Detection**: Runtime fallback may mask underlying issues

### Neutral
- **Increased Code Complexity**: Provider abstraction adds overhead
- **Testing Requirements**: Must test both provider paths
- **Documentation**: Clear documentation needed for provider switching

## Implementation Details

### OpenAI Integration
- **Model**: gpt-4o-mini (optimized for speed/cost)
- **Temperature**: 0.1 (deterministic responses)
- **Timeout**: 30 seconds (prevents hanging)
- **Retry Logic**: Exponential backoff with jitter

### Stub LLM Design
- **Behavior**: Concatenates context sources into readable summary
- **Deterministic**: Same input always produces same output
- **Structure**: Preserves document citations and structure
- **Performance**: Sub-millisecond response times

### Error Handling
```python
try:
    response = openai_client.chat.completions.create(...)
    return response.choices[0].message.content
except OpenAIError as e:
    logger.warning(f"OpenAI failed: {e}")
    return self._generate_fallback_response(query, contexts)
except Exception as e:
    logger.error(f"Unexpected LLM error: {e}")
    raise
```

## Testing Strategy

### Unit Tests
```python
def test_openai_provider():
    provider = LLMProvider(llm_provider="openai", api_key="test-key")
    assert provider.llm_name == "openai:gpt-4o-mini"

def test_stub_provider():
    provider = LLMProvider(llm_provider="stub")
    assert provider.llm_name == "stub"

def test_fallback_behavior():
    # Test with invalid API key
    provider = LLMProvider(llm_provider="openai", api_key="invalid")
    assert provider.llm_name == "stub"  # Fallback occurred
```

### Integration Tests
```python
def test_end_to_end_with_openai():
    # Test full pipeline with real API calls
    engine = RAGEngine()
    response = engine.generate("test query", test_contexts)
    assert response is not None

def test_end_to_end_with_stub():
    # Test full pipeline with stub model
    engine = RAGEngine()
    response = engine.generate("test query", test_contexts)
    assert "stub" in response.lower()  # Stub response
```

## Configuration Examples

### Development (Local, Offline)
```bash
# .env
LLM_PROVIDER=stub
# OPENAI_API_KEY=not_set
```

### Production (Online, OpenAI)
```bash
# .env
LLM_provider=openai
OPENAI_API_KEY=sk-proj-...
```

### Mixed Environment
```bash
# .env.development
LLM_PROVIDER=stub

# .env.production
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
```

## Monitoring Considerations

### Metrics Collection
```python
def generate(self, query: str, contexts: List[Dict]) -> str:
    start_time = time.time()

    try:
        result = self._generate_with_provider(query, contexts)
        generation_time = (time.time() - start_time) * 1000
        self.metrics.add_generation(generation_time)
        return result
    except Exception as e:
        self.metrics.add_error(str(e))
        raise
```

### Health Status Reporting
```python
def health_check(self) -> Dict[str, Any]:
    return {
        "llm_provider": self.llm_name,
        "api_key_configured": bool(self.api_key),
        "fallback_available": isinstance(self.llm, StubLLM),
        "last_error": self.last_error if hasattr(self, 'last_error') else None
    }
```

## Security Considerations

### API Key Protection
- **Storage**: Environment variables only
- **Logging**: Never log API keys or tokens
- **Validation**: Validate API key format before use
- **Scope**: Limited to API permissions required

### Input Sanitization
- **Pre-prompt Validation**: Remove potentially harmful content
- **Context Filtering**: Ensure retrieved chunks are appropriate
- **Output Filtering**: Apply PII masking to generated responses

## Future Considerations

### Additional Providers
- **Ollama**: Local LLM hosting
- **Anthropic**: Claude API integration
- **Google**: Gemini API integration
- **Azure**: Azure OpenAI Service

### Advanced Features
- **Model Routing**: Different models for different query types
- **Cost Optimization**: Provider selection based on query complexity
- **Quality Enhancement**: Multiple provider response aggregation

---

**Status**: Accepted
**Date**: 2025-01-14
**Author**: Development Team
**Reviewers**: Technical Review