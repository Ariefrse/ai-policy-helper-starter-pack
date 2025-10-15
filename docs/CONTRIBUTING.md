# 🤝 Contributing to AI Policy Helper

We welcome contributions! This guide will help you get started contributing to our RAG (Retrieval-Augmented Generation) system.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- Basic knowledge of Python, FastAPI, React/Next.js
- Familiarity with RAG concepts

### Setup Development Environment
```bash
# Clone repository
git clone <your-fork>
cd ai-policy-helper-starter-pack

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start development services
docker compose up --build

# Verify everything works
curl http://localhost:8000/api/health
```

## 📋 How to Contribute

### 1. Find an Issue
- Check [Issues](https://github.com/your-org/ai-policy-helper/issues) for existing work
- Look for "good first issue" labels
- Create a new issue if needed

### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
git checkout -b fix/issue-123
```

### 3. Make Changes
- Follow the coding standards outlined below
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes
```bash
# Run all tests
docker compose run --rm backend pytest -v

# Run specific test suites
docker compose run --rm backend pytest app/tests/test_api.py -v
docker compose run --rm backend pytest app/tests/test_end_to_end.py -v
```

### 5. Submit Pull Request
- Create pull request with clear description
- Link related issues
- Request review from maintainers

## 🏗️ Project Structure

```
ai-policy-helper-starter-pack/
├─ backend/app/           # FastAPI backend
│  ├─ main.py            # Main application entry point
│  ├─ rag.py             # RAG engine implementation
│  ├─ models.py          # Pydantic models
│  ├─ settings.py        # Configuration management
│  ├─ ingest.py          # Document processing
│  └─ tests/             # Test suites
├─ frontend/             # Next.js frontend
│  ├─ app/               # React components
│  │  ├── page.tsx
│  │  └─ layout.tsx
│  ├─ components/        # Reusable components
│  │  ├── Chat.tsx
│  │  └─ AdminPanel.tsx
│  └─ lib/              # Utilities and API client
├─ data/                 # Sample documents
├─ docs/                 # Documentation
├─ tests/                # Integration tests
├─ docker-compose.yml      # Container orchestration
└─ .env.example          # Environment template
```

## 🔧 Development Workflow

### Backend Development

**Local Backend Setup:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Making Changes:**
1. Edit code in `backend/app/`
2. Run tests to verify changes
3. Update documentation if needed
4. Commit changes with descriptive messages

**Testing Backend:**
```bash
# Unit tests
pytest app/tests/test_api.py -v

# Integration tests
pytest app/tests/test_end_to_end.py -v

# All tests
pytest -v
```

### Frontend Development

**Local Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
```

**Making Changes:**
1. Edit components in `frontend/components/` or `frontend/app/`
2. Test in browser
3. Update styles if needed
4. Commit changes

**Testing Frontend:**
```bash
# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest

# Run tests
npm test
```

## 📝 Coding Standards

### Python (Backend)
- **Style**: Follow PEP 8
- **Type Hints**: Use for all function signatures and class attributes
- **Docstrings**: Add comprehensive docstrings for public methods
- **Error Handling**: Use structured logging with try/catch blocks

**Example:**
```python
def ingest_chunks(self, chunks: List[Dict]) -> Tuple[int, int]:
    """Ingest document chunks into the vector store.

    Args:
        chunks: List of document chunks with metadata

    Returns:
        Tuple of (new_docs_count, new_chunks_count)

    Raises:
        ValueError: If chunk format is invalid
    """
    if not chunks:
        return 0, 0

    with self._ingestion_lock:
        # Implementation here
        return self._process_chunks(chunks)
```

### JavaScript/TypeScript (Frontend)
- **Style**: Use ES6+ features with proper formatting
- **TypeScript**: Use type annotations for all functions and components
- **Components**: Use functional components with hooks
- **Error Handling**: Proper error boundaries and try/catch

**Example:**
```typescript
interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  chunks?: Chunk[]
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);

  const send = async () => {
    if (!q.trim()) return;

    try {
      const res = await apiAsk(q);
      const ai: Message = {
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        chunks: res.chunks
      };
      setMessages(m => [...m, ai]);
    } catch (error) {
      setMessages(m => [...m, {
        role: 'assistant',
        content: 'Error: ' + error.message
      }]);
    }
  };
}
```

## 🧪 Testing Standards

### Backend Testing
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test API endpoints and RAG pipeline
- **Performance Tests**: Ensure acceptable response times
- **Coverage**: Maintain >80% test coverage

**Test Structure:**
```python
class TestRAGEngine:
    def setup(self):
        self.engine = RAGEngine()
        self.test_chunks = self._create_test_chunks()

    def test_retrieval_relevant_context(self):
        """Should retrieve relevant chunks for queries."""
        chunks = self.engine.retrieve("shipping policy", k=2)
        assert len(chunks) > 0
        assert all("title" in chunk for chunk in chunks)

    def test_generation_with_context(self):
        """Should generate answer using retrieved context."""
        response = self.engine.generate("test question", self.test_chunks)
        assert response is not None
        assert len(response) > 0
```

### Frontend Testing
- **Component Tests**: Test individual React components
- **Integration Tests**: Test user workflows
- **E2E Tests**: Test complete user journeys
- **Accessibility Tests**: Ensure WCAG compliance

## 📚 Documentation Standards

### README Updates
- Keep README.md up-to-date with latest features
- Include installation and usage instructions
- Add examples for common use cases

### API Documentation
- Use FastAPI's automatic OpenAPI docs
- Add detailed descriptions for endpoints
- Include example requests and responses

### Code Comments
- Explain complex logic with clear comments
- Document architectural decisions in ADRs
- Add inline comments for non-obvious code

## 🔒 Security Guidelines

### Backend Security
- **Input Validation**: Validate all incoming data
- **API Keys**: Never commit secrets to repository
- **Error Messages**: Don't expose sensitive information
- **Rate Limiting**: Consider implementing if needed

### Frontend Security
- **XSS Protection**: Sanitize all user input
- **HTTPS**: Use HTTPS in production
- **API Keys**: Keep out of frontend code
- **Content Security**: Validate file uploads if added

## 🐛 CI/CD Integration

### GitHub Actions (Planned)
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest -v
```

### Pre-commit Hooks (Recommended)
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run on each commit
pre-commit run --all-files
```

## 🎯 Review Process

### Pull Request Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass for new functionality
- [ ] Documentation is updated
- [ ] Security considerations addressed
- [ ] Performance impact considered

### Review Focus Areas
- **Correctness**: Does the code work as intended?
- **Performance**: Are there any performance implications?
- **Security**: Are there any security vulnerabilities?
- **Maintainability**: Is the code easy to understand and maintain?
- **Test Coverage**: Are tests comprehensive?

## 🤝 Community Guidelines

### Code Reviews
- **Be Constructive**: Focus on improvement suggestions
- **Be Thorough**: Check for edge cases and potential issues
- **Be Respectful**: Acknowledge good work and suggest improvements
- **Be Patient**: Provide clear, actionable feedback

### Issue Reporting
- **Search First**: Check if issue already exists
- **Provide Details**: Include steps to reproduce
- **Add Context**: Describe expected vs actual behavior
- **Be Patient**: Allow time for maintainer response

### Feature Requests
- **Use Templates**: Follow issue templates when provided
- **Describe Use Case**: Explain why feature is needed
- **Consider Impact**: Think about broader implications
- **Start Discussion**: Open issue as discussion before PR

## 🏷 Release Process

### Versioning
- **Semantic Versioning**: Use SemVer (MAJOR.MINOR.PATCH)
- **Changelog**: Update CHANGELOG.md with each release
- **Tagging**: Create git tags for releases

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Performance benchmarks updated
- [ ] Security review completed
- [ ] Release notes prepared

## 📞 Getting Help

### Resources
- **Documentation**: [Developer Guide](docs/DEVELOPER_GUIDE.md)
- **API Docs**: [API Playground](docs/API_PLAYGROUND.md)
- **Architecture**: [ADRs](docs/ADRs/)
- **Troubleshooting**: Check issues or create new one

### Communication
- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and ideas
- **Security**: For security-related concerns (private contact)

---

## 🤝 Thank You!

Your contributions make this project better for everyone. Whether you're fixing bugs, adding features, improving documentation, or sharing feedback, we appreciate your help in building the best RAG system possible.

**Happy Contributing!** 🎉