# Contributing to tkr-docusearch

Thank you for your interest in contributing to tkr-docusearch! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Quality Standards](#code-quality-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)

## Development Setup

### Prerequisites

- Python 3.10 or higher
- macOS with M1/M2/M3 chip (for Metal GPU acceleration) or any system with CPU
- Docker and Docker Compose
- Git

### Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/tuckertucker/tkr-docusearch.git
   cd tkr-docusearch
   ```

2. Set up the native worker environment (for GPU mode):
   ```bash
   ./scripts/run-worker-native.sh setup
   ```

3. Install pre-commit hooks:
   ```bash
   .venv-native/bin/pre-commit install
   .venv-native/bin/pre-commit install --hook-type commit-msg
   ```

4. Start the system:
   ```bash
   ./scripts/start-all.sh
   ```

For more details, see [QUICK_START.md](QUICK_START.md).

## Code Quality Standards

This project uses automated code quality tools to maintain consistent, high-quality code.

### Pre-commit Hooks

We use pre-commit hooks to automatically check and format code before commits. The hooks include:

- **black**: Code formatting (line length: 100)
- **isort**: Import sorting
- **autoflake**: Remove unused imports and variables
- **flake8**: Linting and style checking
- **mypy**: Static type checking
- **conventional-pre-commit**: Commit message validation

### Running Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run them manually:

```bash
# Run on all files
.venv-native/bin/pre-commit run --all-files

# Run on staged files only
.venv-native/bin/pre-commit run

# Run a specific hook
.venv-native/bin/pre-commit run black --all-files
```

### Code Formatting

All Python code must be formatted with **black** (line length: 100):

```bash
.venv-native/bin/black src/
```

### Import Sorting

Imports must be sorted using **isort** (compatible with black):

```bash
.venv-native/bin/isort src/
```

### Linting

Code must pass **flake8** checks:

```bash
.venv-native/bin/flake8 src/
```

Configuration is in `pyproject.toml`:
- Max line length: 100
- Ignored errors: E203, E266, E501, W503
- Max complexity: 10

### Type Checking

Use type hints following PEP 484. Check with **mypy**:

```bash
.venv-native/bin/mypy src/
```

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This is enforced by the `conventional-pre-commit` hook.

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semi-colons, etc.)
- **refactor**: Code refactoring (neither fixes a bug nor adds a feature)
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, build process, etc.)
- **ci**: CI/CD changes

### Scope (Optional)

The scope specifies the area of the codebase affected:

- **deps**: Dependencies
- **docker**: Docker configuration
- **embeddings**: Embedding layer
- **storage**: Storage layer
- **processing**: Document processing
- **search**: Search engine
- **api**: API layer
- **ui**: User interface
- **scripts**: Management scripts

### Examples

Good commit messages:

```
feat(embeddings): add batch processing for images

fix(storage): resolve ChromaDB connection timeout issue

docs: update QUICK_START with GPU setup instructions

chore(deps): update torch to 2.8.0 for CVE patch

refactor(search): simplify two-stage ranking pipeline
```

Bad commit messages:

```
fixed bug
Update README
WIP
asdf
```

### Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the footer or append `!` after the type:

```
feat(api)!: change endpoint response format

BREAKING CHANGE: The /search endpoint now returns a different JSON structure.
```

## Testing

### Running Tests

Run all tests:

```bash
.venv-native/bin/pytest
```

Run tests with coverage:

```bash
.venv-native/bin/pytest --cov=src --cov-report=term-missing
```

Run specific test file:

```bash
.venv-native/bin/pytest src/embeddings/test_embeddings.py
```

### Writing Tests

- All new features must include tests
- Tests should follow the naming pattern `test_*.py`
- Use pytest fixtures for common setup
- Aim for high test coverage (>80%)

## Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes** following the code quality standards

3. **Run pre-commit hooks** to ensure code quality:
   ```bash
   .venv-native/bin/pre-commit run --all-files
   ```

4. **Run tests** to ensure nothing is broken:
   ```bash
   .venv-native/bin/pytest
   ```

5. **Commit your changes** with conventional commit messages:
   ```bash
   git add .
   git commit -m "feat(scope): description of changes"
   ```

6. **Push to your fork** and create a pull request:
   ```bash
   git push origin feat/your-feature-name
   ```

7. **Fill out the PR template** with:
   - Clear description of changes
   - Why the changes are needed
   - Testing performed
   - Screenshots (if UI changes)

8. **Address review feedback** by making additional commits

9. **Squash and merge** once approved (maintainer will do this)

## Code Style

### Python Style

Follow these Python conventions:

1. **PEP 8**: Standard Python style guide
2. **PEP 484**: Type hints for function signatures
3. **PEP 257**: Docstring conventions (Google style)
4. **Line length**: 100 characters (enforced by black)

### Docstring Format (Google Style)

```python
def embed_images(self, images: List[Image.Image]) -> torch.Tensor:
    """Embed a list of images using the ColPali model.

    Args:
        images: List of PIL Image objects to embed.

    Returns:
        Tensor of shape (batch_size, seq_length, embedding_dim) containing
        the multi-vector embeddings for each image.

    Raises:
        ValueError: If images list is empty.
        RuntimeError: If model inference fails.

    Example:
        >>> from PIL import Image
        >>> engine = ColPaliEngine()
        >>> images = [Image.open("doc1.png")]
        >>> embeddings = engine.embed_images(images)
        >>> print(embeddings.shape)
        torch.Size([1, 1031, 128])
    """
    if not images:
        raise ValueError("Images list cannot be empty")
    # Implementation...
```

### Logging

Use `structlog` for all logging (PEP 337):

```python
import structlog

logger = structlog.get_logger(__name__)

def process_document(doc_path: str):
    logger.info("processing_document_start", path=doc_path)
    try:
        # Process document
        logger.info("processing_document_complete", path=doc_path)
    except Exception as e:
        logger.error("processing_document_failed", path=doc_path, error=str(e))
        raise
```

### Directory Structure

Follow the established project structure:

```
tkr-docusearch/
├── src/               # Source code
│   ├── embeddings/    # ColPali embedding layer
│   ├── storage/       # ChromaDB storage layer
│   ├── processing/    # Document processing
│   ├── search/        # Two-stage search engine
│   └── config/        # Configuration modules
├── scripts/           # Management scripts
├── docker/            # Docker configuration
├── docs/              # Documentation
└── data/              # Data storage (gitignored)
```

## Automated Dependency Updates

We use Dependabot to automatically update dependencies:

- **Python packages**: Weekly updates on Mondays
- **GitHub Actions**: Weekly updates on Mondays
- **Docker images**: Weekly updates on Mondays

Dependabot PRs are automatically labeled and grouped by update type (minor/patch vs major).

## Questions or Issues?

- Open an issue on GitHub for bugs or feature requests
- Check existing documentation in the `docs/` directory
- Review the [QUICK_START.md](QUICK_START.md) for setup help

## License

By contributing to tkr-docusearch, you agree that your contributions will be licensed under the MIT License.
