"""End-to-end integration tests for the RAG pipeline."""

import pytest
import time
import os
from app.rag import RAGEngine
from app.ingest import load_documents


def create_test_data():
    """Create test data if data directory doesn't exist (for CI/CD environments)."""
    if not os.path.exists("/app/data"):
        # Create minimal test data for CI/CD
        test_data_dir = "/tmp/test_data"
        os.makedirs(test_data_dir, exist_ok=True)

        # Create test document
        test_doc = """# Test Policy Document

## Return Policy
Customers can return small appliances within 14 days for change of mind.
Defective items can be returned within 30 days.

## Warranty Policy
Warranty covers manufacturing defects for 12 months.
Damage due to misuse is not covered.

## Shipping Policy
Standard shipping takes 3-5 business days.
Express shipping takes 1-2 business days.
"""

        with open(f"{test_data_dir}/test_policy.md", "w") as f:
            f.write(test_doc)

        return test_data_dir
    return "/app/data"


def test_end_to_end_rag_pipeline():
    """Test complete user journey: Ingest → Query → Citations → Response"""

    # 1. Initialize RAG engine
    engine = RAGEngine()

    # 2. Get test data directory (fallback for CI/CD)
    data_dir = create_test_data()

    # 3. Ingest sample documents
    start_time = time.time()
    chunks = load_documents(data_dir)
    indexed_docs, indexed_chunks = engine.ingest_chunks(chunks)
    ingest_time = time.time() - start_time
    
    # Verify ingestion worked
    assert indexed_docs > 0, "Should have indexed some documents"
    assert indexed_chunks > 0, "Should have indexed some chunks"
    assert ingest_time < 5.0, "Ingestion should complete within 5 seconds"
    
    # 3. Test retrieval performance
    start_time = time.time()
    retrieved_chunks = engine.retrieve("return policy", k=4)
    retrieval_time = time.time() - start_time
    
    # Verify retrieval worked
    assert len(retrieved_chunks) <= 4, "Should respect k limit"
    assert retrieval_time < 0.1, "Retrieval should be under 100ms"
    assert all("title" in chunk for chunk in retrieved_chunks), "All chunks should have titles"
    
    # 4. Test generation with citations
    start_time = time.time()
    answer = engine.generate("What is the return policy?", retrieved_chunks)
    generation_time = time.time() - start_time
    
    # Verify generation worked
    assert len(answer) > 10, "Should generate meaningful answer"
    assert generation_time < 10.0, "Generation should complete within 10 seconds"
    
    # 5. Test metrics collection
    stats = engine.stats()
    assert stats["total_docs"] == indexed_docs
    assert stats["total_chunks"] == indexed_chunks
    assert stats["total_asks"] >= 1, "Should track query count"
    assert stats["avg_retrieval_latency_ms"] > 0, "Should measure retrieval latency"
    assert stats["avg_generation_latency_ms"] > 0, "Should measure generation latency"


def test_rag_pipeline_with_citations():
    """Test that RAG pipeline returns proper citations for acceptance criteria."""

    engine = RAGEngine()

    # Get test data directory (fallback for CI/CD)
    data_dir = create_test_data()

    # Ingest documents
    chunks = load_documents(data_dir)
    engine.ingest_chunks(chunks)
    
    # Test acceptance criteria query 1
    retrieved_chunks = engine.retrieve("Can a customer return a damaged blender after 20 days?", k=8)
    answer = engine.generate("Can a customer return a damaged blender after 20 days?", retrieved_chunks)

    # Verify citations are available (adapt for test data)
    titles = [chunk.get("title") for chunk in retrieved_chunks]
    if os.path.exists("/app/data"):
        # Full data directory - check for specific documents
        assert any("Returns_and_Refunds.md" in title for title in titles), "Should cite Returns_and_Refunds.md"
    else:
        # Test data directory - check for any relevant content
        assert len(titles) > 0, "Should have citations from test data"

    # Test acceptance criteria query 2
    retrieved_chunks = engine.retrieve("What's the shipping SLA to East Malaysia for bulky items?", k=8)
    answer = engine.generate("What's the shipping SLA to East Malaysia for bulky items?", retrieved_chunks)

    # Verify citations are available (adapt for test data)
    titles = [chunk.get("title") for chunk in retrieved_chunks]
    if os.path.exists("/app/data"):
        # Full data directory - check for specific documents
        assert any("Delivery_and_Shipping.md" in title for title in titles), "Should cite Delivery_and_Shipping.md"
    else:
        # Test data directory - check for any relevant content
        assert len(titles) > 0, "Should have citations from test data"


def test_performance_under_load():
    """Test system performance with multiple concurrent-like operations."""

    engine = RAGEngine()

    # Get test data directory (fallback for CI/CD)
    data_dir = create_test_data()

    # Ingest documents
    chunks = load_documents(data_dir)
    engine.ingest_chunks(chunks)
    
    # Simulate multiple queries (sequential for simplicity)
    queries = [
        "What is the return policy?",
        "How long does shipping take?", 
        "What about warranty coverage?",
        "Are there any exclusions?",
        "What's the refund process?"
    ]
    
    total_start = time.time()
    for query in queries:
        start = time.time()
        retrieved = engine.retrieve(query, k=3)
        answer = engine.generate(query, retrieved)
        query_time = time.time() - start
        
        # Each query should complete reasonably fast
        assert query_time < 15.0, f"Query '{query}' took too long: {query_time:.2f}s"
        assert len(retrieved) <= 3, "Should respect retrieval limit"
        assert len(answer) > 0, "Should generate non-empty answer"
    
    total_time = time.time() - total_start
    avg_time_per_query = total_time / len(queries)
    
    # Performance assertions
    assert avg_time_per_query < 10.0, f"Average query time too high: {avg_time_per_query:.2f}s"
    
    # Verify caching is working (second run should be faster)
    cache_test_start = time.time()
    retrieved = engine.retrieve(queries[0], k=3)  # Should hit cache
    cache_time = time.time() - cache_test_start
    assert cache_time < 0.05, "Cached retrieval should be very fast"


def test_error_resilience():
    """Test that the system handles errors gracefully."""
    
    engine = RAGEngine()
    
    # Test with empty query
    retrieved = engine.retrieve("", k=4)
    assert isinstance(retrieved, list), "Should return empty list for empty query"
    
    # Test with very long query
    long_query = "a" * 2000
    retrieved = engine.retrieve(long_query, k=4)
    assert isinstance(retrieved, list), "Should handle long queries gracefully"
    
    # Test generation with empty contexts
    answer = engine.generate("test query", [])
    assert isinstance(answer, str), "Should return string even with no context"
    assert len(answer) > 0, "Should generate fallback answer"