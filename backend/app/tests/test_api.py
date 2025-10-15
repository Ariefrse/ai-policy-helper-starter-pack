def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

def test_service_status(client):
    """Test service status endpoint returns expected structure."""
    r = client.get("/api/service-status")
    assert r.status_code == 200
    data = r.json()

    # Verify required fields exist
    assert "services" in data
    assert "any_degraded" in data
    assert "all_healthy" in data
    assert "status_message" in data

    # Verify services structure
    services = data["services"]
    assert "vector_store" in services
    assert "llm" in services

    # Verify each service has required fields
    for service_name, service_data in services.items():
        assert "healthy" in service_data
        assert "type" in service_data
        assert "degraded" in service_data

def test_ingest_and_ask(client):
    r = client.post("/api/ingest")
    assert r.status_code == 200
    # Ask a deterministic question
    r2 = client.post("/api/ask", json={"query":"What is the refund window for small appliances?"})
    assert r2.status_code == 200
    data = r2.json()
    assert "citations" in data and len(data["citations"]) > 0
    assert "answer" in data and isinstance(data["answer"], str)
