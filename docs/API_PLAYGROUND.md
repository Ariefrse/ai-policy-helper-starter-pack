# 🎮 API Playground

Interactive testing interface for the AI Policy Helper API.

## 🚀 Quick Start

### Base URLs
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Vector DB UI**: http://localhost:6333

## 🧪 Interactive Examples

### 1. Health Check

**Test the system status:**
```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{
  "status": "ok"
}
```

### 2. Document Ingestion

**Ingest all sample documents:**
```bash
curl -X POST http://localhost:8000/api/ingest
```

**Expected Response:**
```json
{
  "indexed_docs": 6,
  "indexed_chunks": 12
}
```

### 3. Ask Questions

**Basic question:**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the warranty period?"}'
```

**Question with custom k value:**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "shipping policy", "k": 6}'
```

### 4. Get Metrics

**System performance metrics:**
```bash
curl http://localhost:8000/api/metrics
```

**Expected Response:**
```json
{
  "total_docs": 6,
  "total_chunks": 12,
  "avg_retrieval_latency_ms": 12.3,
  "avg_generation_latency_ms": 2750.8,
  "embedding_model": "local",
  "llm_model": "openai:gpt-4o-mini"
}
```

## 🎯 Real-World Scenarios

### Scenario 1: Product Information

**Question:** "What products do you have available?"

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "product catalog PowerBlend CleanMax AirFry"}'
```

**Expected Response:**
```json
{
  "query": "product catalog PowerBlend CleanMax AirFry",
  "answer": "- **Product Name**: PowerBlend 100\n  - **SKU**: BLNDR-100\n  - **Price**: 399 MYR\n  - **Warranty**: 12 months\n  - **Category**: Kitchen\n  - **Availability**: In stock\n\n- **Product Name**: CleanMax 200\n  - **SKU**: VCUUM-200\n  - **Price**: 599 MYR\n  - **Warranty**: 24 months\n  - **Category**: Home\n  - **Availability**: In stock",
  "citations": [
    {"title": "Product_Catalog.md", "section": "Product Catalog"}
  ],
  "chunks": [...]
}
```

### Scenario 2: Returns & Warranty

**Question:** "Can I return a damaged blender after 20 days?"

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Can a customer return a damaged blender after 20 days?"}'
```

### Scenario 3: Shipping Information

**Question:** "What's the shipping SLA to East Malaysia for bulky items?"

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "shipping SLA East Malaysia bulky items"}'
```

## 🔧 Advanced Testing

### Error Handling

**Invalid query (too long):**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "' + 'a' * 1001 + '"}'  # 1001 chars (over limit)
```

**Expected Response:** HTTP 422 with validation error

### Edge Cases

**Empty query:**
```bash
curl -X POST http://localhost/8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": ""}'
```

**Malformed JSON:**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "test"'  # Missing closing brace
```

## 📊 Performance Testing

### Load Testing with cURL

**Concurrent requests:**
```bash
# Test 10 concurrent requests
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/ask \
    -H "Content-Type: application/json" \
    -d '{"query": "test query '$i'"}' &
done
wait
```

### Using wrk for Load Testing

```bash
# Install wrk (macOS)
brew install wrk

# Run load test
wrk -t12 -c4 -d30s --timeout=10s \
  --script=<(echo 'POST /api/ask HTTP/1.1
Host: localhost:8000
Content-Type: application/json
{"query": "load test question"}') \
  http://localhost:8000
```

## 🛠️ Debug Endpoints

### Vector Store Inspection

**Test retrieval without generation:**
```bash
curl -X POST http://localhost:8000/api/debug/vector-store \
  -H "Content-Type: application/json" \
  -d '{"query": "shipping policy", "k": 3}'
```

### Embedding Testing

**Test embedding generation:**
```bash
curl -X POST http://localhost:8000/api/debug/embeddings \
  -H "Content-Type: application/json" \
  -d '{"text": "delivery and shipping policy"}'
```

## 📝 Request Examples

### Python Requests

```python
import requests

# Ask a question
response = requests.post(
    "http://localhost:8000/api/ask",
    json={"query": "What is the warranty period?"}
)
print(response.json())

# Get metrics
metrics = requests.get("http://localhost:8000/api/metrics")
print(metrics.json())
```

### JavaScript (Browser Console)

```javascript
// Ask a question
fetch("http://localhost:8000/api/ask", {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({
    query: "What products do you have?"
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### Node.js

```javascript
const fetch = require('node-fetch');

// Ask a question
fetch('http://localhost:8000/api/ask', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: 'Shipping policy for East Malaysia',
    k: 5
  })
})
.then(res => res.json())
.then(console.log);
```

## 🔍 Response Analysis

### Understanding Citations

Each response includes:
- **`citations`**: Source documents that informed the answer
- **`chunks`**: Actual text snippets used as context
- **`metrics`**: Performance measurements

### Sample Response Breakdown

```json
{
  "query": "shipping policy",
  "answer": "East Malaysia shipping takes 5-8 business days...",
  "citations": [
    {"title": "Delivery_and_Shipping.md", "section": "SLA"}
  ],
  "chunks": [
    {
      "title": "Delivery_and_Shipping.md",
      "section": "SLA",
      "text": "## SLA - West Malaysia: 2–4 business days..."
    }
  ],
  "metrics": {
    "retrieval_ms": 12.3,
    "generation_ms": 2750.8
  }
}
```

## 🧪 Test Data

### Sample Queries

```bash
# Product questions
"What products do you have?"
"How much does PowerBlend 100 cost?"
"Is AirFry Pro in stock?"

# Policy questions
"What is the return policy?"
"How long is the warranty?"
"Do you ship to East Malaysia?"

# General questions
"What are your business hours?"
"How do I contact support?"
```

## 🎯 Tips for Testing

1. **Start with health checks** - Verify all services are running
2. **Test ingestion first** - Ensure documents are indexed
3. **Use specific queries** - Better retrieval results
4. **Check citations** - Verify sources are correct
5. **Monitor metrics** - Watch performance over time
6. **Test edge cases** - Empty queries, long queries, special characters

---

**Need help?** Check the [Developer Guide](./DEVELOPER_GUIDE.md) or create an issue!