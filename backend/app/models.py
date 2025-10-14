from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import re

class IngestResponse(BaseModel):
    indexed_docs: int
    indexed_chunks: int

class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    k: int | None = Field(default=4, ge=1, le=20, description="Number of chunks to retrieve")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty or only whitespace')
        
        # Remove excessive whitespace
        v = re.sub(r'\s+', ' ', v.strip())
        
        # Check for potential injection patterns
        suspicious_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*='
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Query contains potentially malicious content')
        
        return v

class Citation(BaseModel):
    title: str
    section: str | None = None

class Chunk(BaseModel):
    title: str
    section: str | None = None
    text: str

class AskResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    chunks: List[Chunk]
    metrics: Dict[str, Any]

class MetricsResponse(BaseModel):
    total_docs: int
    total_chunks: int
    avg_retrieval_latency_ms: float
    avg_generation_latency_ms: float
    p95_retrieval_latency_ms: float
    p95_generation_latency_ms: float
    total_asks: int
    total_ingests: int
    embedding_model: str
    llm_model: str

class FeedbackRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    answer: str = Field(..., min_length=1, max_length=5000)
    rating: Optional[int] = Field(None, ge=0, le=1, description="1 for thumbs-up, 0 for thumbs-down")
    comment: Optional[str] = Field(None, max_length=2000, description="Optional feedback comment")
    
    @field_validator('query', 'answer', 'comment')
    @classmethod
    def validate_text_fields(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Text fields cannot be empty or only whitespace')
        return re.sub(r'\s+', ' ', v.strip())

class FeedbackResponse(BaseModel):
    ok: bool
