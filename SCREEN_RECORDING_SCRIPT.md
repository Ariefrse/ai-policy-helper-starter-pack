# Screen Recording Script (2-5 minutes)

## Pre-Recording Checklist
- [ ] Close unnecessary browser tabs
- [ ] Set browser zoom to 100%
- [ ] Clear browser console
- [ ] Open terminal with clean session
- [ ] Prepare timer (aim for 3-4 minutes)
- [ ] Test microphone (optional but recommended)

---

## Script Timeline

### Part 1: Introduction (0:00-0:30) - 30 seconds

**Action:** Show project directory in terminal

```bash
cd /Users/ariefrse/Desktop/ai-policy-helper-starter-pack
ls -la
```

**Narration:**
> "Hi, this is my submission for the AI Policy Helper take-home assignment.
> I'll demonstrate the key features: document ingestion, RAG-based Q&A with citations,
> and the expandable chunks feature. Let's start by launching the application."

---

### Part 2: Docker Setup (0:30-1:00) - 30 seconds

**Action:** Show docker-compose.yml and start services

```bash
# Show the compose file (optional, if time permits)
cat docker-compose.yml | head -20

# Start services (if not running) OR show they're already running
docker compose ps
```

**Narration:**
> "The entire stack runs with one command: docker compose up.
> As you can see, all services are running: FastAPI backend on port 8000,
> Next.js frontend on 3001, and Qdrant vector database on 6333."

**Browser:** Navigate to http://localhost:3001

---

### Part 3: Admin Panel & Ingestion (1:00-1:45) - 45 seconds

**Action:** Use admin panel to ingest documents

1. **Show UI homepage**
   - Point out the clean, simple interface
   - Show the "How to test" instructions

2. **Click "Ingest sample docs" button**
   - Wait for success message
   - Show the metrics refresh

3. **Click "Refresh metrics" button**
   - Point out key metrics:
     - 6 documents indexed
     - 60+ chunks created
     - Average retrieval latency ~18ms
     - Embedding model: local-384
     - LLM model: openai:gpt-4o-mini

**Narration:**
> "First, I'll ingest the sample policy documents. The system loads markdown files
> from the data directory, splits them into sections, and chunks them for RAG.
> After ingestion, we can see 6 documents with 60 chunks indexed.
> The system tracks latency metrics - retrieval is fast at ~18ms,
> and we're using OpenAI's gpt-4o-mini for generation."

---

### Part 4: Acceptance Query #1 (1:45-2:30) - 45 seconds

**Action:** Test first acceptance criteria question

**Type in chat:**
```
Can a customer return a damaged blender after 20 days?
```

**Wait for response, then:**

1. **Show the answer**
   - Point out it references the policies

2. **Highlight citation badges**
   - Point to "Returns_and_Refunds.md" badge
   - Point to "Warranty_Policy.md" badge
   - Hover to show section names

3. **Expand "View supporting chunks"**
   - Show the detailed text excerpts
   - Point out highlighted keywords (return, damaged, 20, days)
   - Show title and section headers

**Narration:**
> "Let's ask the first acceptance question: Can a customer return a damaged blender after 20 days?
> The answer correctly references our policies. Notice the citation badges here -
> we have Returns and Refunds policy, and Warranty Policy.
> When I expand the supporting chunks, you can see the exact text used to generate this answer,
> with relevant keywords highlighted. This transparency is crucial for trust."

---

### Part 5: Acceptance Query #2 (2:30-3:15) - 45 seconds

**Action:** Test second acceptance criteria question

**Type in chat:**
```
What's the shipping SLA to East Malaysia for bulky items?
```

**Wait for response, then:**

1. **Show the answer**
   - Point out specific SLA details mentioned

2. **Highlight citation badges**
   - Point to "Delivery_and_Shipping.md" badge
   - Note it appears multiple times (different sections)

3. **Expand chunks again**
   - Show the section about East Malaysia
   - Show the bulky items surcharge mention
   - Point out the specific SLA timeframes

**Narration:**
> "Second acceptance question: What's the shipping SLA to East Malaysia for bulky items?
> The system correctly cites the Delivery and Shipping policy.
> In the supporting chunks, we can see the specific SLA for East Malaysia -
> 5 to 7 business days for standard items, with a bulky item surcharge mentioned here.
> The retrieval correctly found the most relevant sections."

---

### Part 6: Additional Features (3:15-3:45) - 30 seconds

**Action:** Demonstrate other features

1. **Show feedback buttons**
   - Click thumbs up on one answer
   - Explain feedback collection

2. **Show copy button**
   - Copy an answer to clipboard

3. **Test another quick question (optional)**
   ```
   What are the warranty exclusions?
   ```

**Narration:**
> "The UI also includes feedback buttons for thumbs up and down,
> which logs user preferences for later analysis.
> Users can copy answers to clipboard.
> Let me quickly test one more question about warranty exclusions...
> Again, proper citations with expandable source chunks."

---

### Part 7: Backend & Tests (3:45-4:30) - 45 seconds

**Action:** Show backend API and tests

**Terminal commands:**
```bash
# Show API documentation
open http://localhost:8000/docs
# OR show in browser if already open

# Run tests
docker compose run --rm backend pytest -v

# Show test results
```

**Narration:**
> "The backend exposes a FastAPI interface with Swagger documentation at /docs.
> All endpoints are documented here: health checks, metrics, ingestion, and queries.
> For testing, I've written comprehensive test suites -
> as you can see, all 8 tests pass, covering unit tests, integration tests,
> and the two acceptance criteria we just demonstrated.
> Tests verify citation accuracy, performance benchmarks, and error handling."

---

### Part 8: Architecture & Closing (4:30-5:00) - 30 seconds

**Action:** Show README or architecture

**Open in editor:**
```bash
# Show architecture diagram in README
open AI_Policy_Helper_README.md
# Scroll to architecture section (lines 108-148)
```

**Narration:**
> "The architecture is documented in the README with an ASCII diagram
> showing the full stack: Next.js frontend, FastAPI backend with RAG engine,
> and Qdrant vector database.
> Key features include input validation, error handling with fallbacks,
> LRU caching to prevent memory leaks, and structured logging for observability.
> The system is production-ready with thread-safe operations and comprehensive security measures.
> Thank you for reviewing my submission!"

---

## Quick Tips for Recording

### If You Run Out of Time
**Minimum viable demo (2 minutes):**
1. Show UI (15s)
2. Ingest docs (15s)
3. Query 1 with citations (30s)
4. Query 2 with citations (30s)
5. Show tests passing (20s)
6. Closing (10s)

### If You Have Extra Time
**Extended features to show:**
- View Qdrant UI at http://localhost:6333
- Show vector collection details
- Demonstrate error handling (invalid query)
- Show PII masking in action
- Display Prometheus metrics at http://localhost:9090

### Recording Tools
- **macOS:** QuickTime Player (⌘ + Space, type "QuickTime")
  - File → New Screen Recording
  - Select microphone if narrating
  - Click record, then select screen area
  - Stop with menu bar icon

- **Alternative:** OBS Studio (free, cross-platform)
- **Alternative:** Loom (browser-based, easy sharing)

### After Recording
1. **Review the video** - Make sure audio is clear
2. **Check timestamps** - Ensure demo flows smoothly
3. **Verify acceptance criteria** - Both questions answered with correct citations
4. **File size** - Compress if needed (should be under 100MB)
5. **Upload** - YouTube (unlisted), Loom, or Google Drive

---

## Troubleshooting

**If services aren't running:**
```bash
docker compose up --build
# Wait 30 seconds for services to start
```

**If ingestion shows 0 documents:**
```bash
# Check data directory
ls -la data/
# Should show 6 .md files

# Try ingesting via curl
curl -X POST http://localhost:8000/api/ingest
```

**If frontend won't load:**
```bash
# Check frontend logs
docker compose logs frontend

# Frontend should be on port 3001 (not 3000)
open http://localhost:3001
```

**If citations are wrong:**
```bash
# Re-ingest documents
curl -X POST http://localhost:8000/api/ingest

# Check Qdrant has data
curl http://localhost:6333/collections/policy_helper
```

---

## Post-Recording Checklist

- [ ] Video length is 2-5 minutes
- [ ] Both acceptance questions demonstrated
- [ ] Citations shown for both questions
- [ ] Chunks expanded to show source text
- [ ] Tests shown passing
- [ ] Audio is clear (if narrated)
- [ ] Video uploaded and link ready
- [ ] Video accessibility: unlisted or public

---

## Example Opening Lines (Choose One)

**Option 1 - Technical:**
> "This is my AI Policy Helper submission. I've built a local-first RAG system
> using FastAPI, Next.js, and Qdrant. Let me show you the core features."

**Option 2 - Business-Focused:**
> "Hi, this demo shows a production-ready policy assistant with RAG-based answers
> and full citation transparency. Let me walk you through the key features."

**Option 3 - Concise:**
> "AI Policy Helper demo. Document ingestion, RAG queries, and citation tracking
> in under 4 minutes. Let's go."

---

## Example Closing Lines (Choose One)

**Option 1 - Technical:**
> "All tests pass, architecture is documented, and the system is production-ready
> with security, caching, and observability. Thanks for watching!"

**Option 2 - Business-Focused:**
> "The system provides accurate answers with full transparency through citations,
> making it trustworthy for customer service teams. Thank you!"

**Option 3 - Concise:**
> "All acceptance criteria met. Tests pass. Production-ready. Thank you!"

---

## Video Upload Recommendations

### YouTube (Unlisted)
1. Upload to YouTube
2. Set to "Unlisted" (not Private, not Public)
3. Add title: "AI Policy Helper - Take-Home Demo"
4. Copy shareable link

### Loom
1. Record directly in Loom
2. Share link (no download needed)
3. Set expiration if desired

### Google Drive
1. Upload video file
2. Set sharing to "Anyone with link can view"
3. Copy shareable link

**Add link to README section for submission!**
