# Contributing to Rural India AI

Thank you for your interest in building AI systems for rural India!

## Development Setup

```bash
# Clone and setup
git clone https://github.com/your-org/rural-india-ai.git
cd rural-india-ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dev dependencies
pip install -e ".[dev]"
pip install pre-commit

# Setup pre-commit hooks
pre-commit install
```

## Code Style

- **Python**: Follow PEP 8 with Black formatter
  ```bash
  black edge_node/ tests/ *.py
  ```

- **Type Hints**: Use type annotations where possible
  ```python
  async def process_query(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
      pass
  ```

- **Docstrings**: Use Google-style docstrings
  ```python
  """Summary line.
  
  Longer description with examples.
  
  Args:
      param: Description
      
  Returns:
      Description of return value
  """
  ```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=edge_node --cov-report=html

# Run async tests
pytest tests/test_async.py -v -s
```

## Git Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test: `pytest tests/ -v`
3. Format code: `black edge_node/ tests/`
4. Commit with clear message: `git commit -m "Feature: describe change"`
5. Push and create Pull Request

## Phase Roadmap

- **Phase 1** (Current): Edge-Native Infrastructure ✅
- **Phase 2**: Voice-First Interface (WhatsApp, IVR, Indic ASR/TTS)
- **Phase 3**: Local Data Ingestion (Vector DB, RAG, India Stack)
- **Phase 4**: Domain-Specific Agents (Krishi, Asha, Yojana, Sahukar)
- **Phase 5**: Trust & Guardrails (Consent, Misinformation Detection)
- **Phase 6**: Deployment & Observability (OTA, Dashboards)

## Community

- Report issues via GitHub Issues
- Discuss architecture in Discussions
- Ask questions in the community forum

Thanks for contributing! 🚀
