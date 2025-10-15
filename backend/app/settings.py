from pydantic import BaseModel
import os
from typing import Optional

class Settings(BaseModel):
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "local-384")
    llm_provider: str = os.getenv("LLM_PROVIDER", "stub")  # stub | openai | ollama
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    vector_store: str = os.getenv("VECTOR_STORE", "qdrant")  # qdrant | memory
    collection_name: str = os.getenv("COLLECTION_NAME", "policy_helper")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "700"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "80"))
    data_dir: str = os.getenv("DATA_DIR", "/app/data")
    mask_pii: bool = os.getenv("MASK_PII", "true").lower() in ("1","true","yes")
    # CORS settings
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
    environment: str = os.getenv("ENVIRONMENT", "development")
    # New configuration options
    default_embedding_dim: int = int(os.getenv("DEFAULT_EMBEDDING_DIM", "384"))
    metrics_buffer_size: int = int(os.getenv("METRICS_BUFFER_SIZE", "1000"))
    vector_search_k: int = int(os.getenv("VECTOR_SEARCH_K", "4"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    base_delay: float = float(os.getenv("BASE_DELAY", "1.0"))
    # Security settings
    monitoring_api_key: Optional[str] = os.getenv("MONITORING_API_KEY")

settings = Settings()
