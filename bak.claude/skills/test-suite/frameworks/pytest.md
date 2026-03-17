# pytest

## Setup

```bash
pip install pytest pytest-cov pytest-asyncio
```

```ini
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = "-v --strict-markers"
```

## Test Structure

```python
import pytest

class TestUserService:
    """Tests for the UserService class."""

    def test_creates_user_with_valid_email(self, user_service):
        user = user_service.create(email="valid@test.com")
        assert user.email == "valid@test.com"

    def test_raises_for_duplicate_email(self, user_service):
        user_service.create(email="dup@test.com")
        with pytest.raises(DuplicateError, match="already exists"):
            user_service.create(email="dup@test.com")
```

## Fixtures (conftest.py)

Fixtures are pytest's dependency injection system. Define them in `conftest.py`
and pytest auto-discovers them:

```python
# tests/conftest.py
import pytest
from pathlib import Path
from tempfile import mkdtemp
from shutil import rmtree

@pytest.fixture
def tmp_dir():
    """Create and clean up a temporary directory."""
    path = Path(mkdtemp(prefix="test-"))
    yield path
    rmtree(path, ignore_errors=True)

@pytest.fixture
def store(tmp_dir):
    """Create a store backed by a temp directory."""
    return Store(data_dir=tmp_dir)

@pytest.fixture
def service(store):
    """Create a service with a test store."""
    return UserService(store=store)
```

### Fixture Scopes

```python
@pytest.fixture(scope="function")   # Default — fresh per test
@pytest.fixture(scope="class")      # Shared within test class
@pytest.fixture(scope="module")     # Shared within test file
@pytest.fixture(scope="session")    # Shared across entire run
```

Use `function` scope by default. Only use wider scopes for expensive setup
(database creation, server startup) that is truly safe to share.

## Parametrize

```python
@pytest.mark.parametrize("input,expected", [
    ("", False),
    ("abc", False),
    ("abc123", True),
    ("123", True),
], ids=["empty", "no-digits", "mixed", "digits-only"])
def test_is_valid(input, expected):
    assert is_valid(input) == expected
```

## Async Testing

```python
# With pytest-asyncio and asyncio_mode = "auto"
async def test_async_operation(service):
    result = await service.fetch_data()
    assert result is not None
```

## Markers

```python
@pytest.mark.slow          # Custom marker
@pytest.mark.integration   # Custom marker
@pytest.mark.skip(reason="known bug #123")
@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
@pytest.mark.xfail(reason="not yet implemented")
```

```bash
pytest -m "not slow"           # Skip slow tests
pytest -m integration          # Run only integration tests
```

## Directory Structure

```
tests/
├── conftest.py               # Shared fixtures
├── unit/
│   ├── conftest.py            # Unit-specific fixtures
│   ├── test_parser.py
│   └── test_validator.py
├── integration/
│   ├── conftest.py            # Integration fixtures (DB, etc.)
│   └── test_user_flow.py
└── e2e/
    ├── conftest.py            # E2E fixtures (server, client)
    └── test_api_flows.py
```

## Conventions

### Assertion Style

```python
# Good — clear, informative failures
assert user.email == "expected@test.com"
assert len(items) == 3
assert "error" in response.text.lower()

# Better for complex checks — use pytest helpers
with pytest.raises(ValueError, match="invalid email"):
    validate_email("bad")

# Collections
assert set(result) == {"a", "b", "c"}  # Order-independent
assert result == pytest.approx(3.14, abs=0.01)  # Float comparison
```

### Factory Pattern

```python
def make_user(**overrides) -> User:
    defaults = {
        "name": "Test User",
        "email": "test@example.com",
        "role": "member",
    }
    return User(**(defaults | overrides))
```

### Testing Exceptions

```python
def test_raises_with_context():
    with pytest.raises(AuthError) as exc_info:
        service.authenticate(bad_token)
    assert "expired" in str(exc_info.value)
    assert exc_info.value.token == bad_token
```

### Temporary Files

```python
def test_file_processing(tmp_path):  # Built-in fixture
    input_file = tmp_path / "input.txt"
    input_file.write_text("test data")
    result = process(input_file)
    assert result.success
```
