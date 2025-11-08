# CI/CD Workflows

This directory contains GitHub Actions workflows that enforce quality standards for the DocuSearch project.

## Overview

The CI/CD system includes three main workflows:

1. **Test Coverage** - Ensures code is adequately tested
2. **Code Quality** - Enforces coding standards and type safety
3. **Accessibility** - Validates WCAG 2.1 AA compliance

All workflows run automatically on pushes to `main` and `develop` branches, as well as on pull requests.

## Workflows

### 1. Test Coverage (`test-coverage.yml`)

**Purpose:** Enforce minimum 70% test coverage for both backend and frontend.

**What it does:**
- Runs backend tests with pytest and coverage reporting
- Runs frontend tests with Vitest and coverage reporting
- Uploads coverage reports as artifacts
- Generates coverage summaries in job outputs
- **Fails if coverage drops below 70%**

**Backend Coverage:**
- Tool: pytest + pytest-cov
- Threshold: 70% (lines, statements, branches, functions)
- Config: `pyproject.toml`
- Command: `pytest tests/ --cov=src --cov-fail-under=70`

**Frontend Coverage:**
- Tool: Vitest + v8 coverage provider
- Threshold: 70% (lines, statements, branches, functions)
- Config: `frontend/vitest.config.js`
- Command: `npm run test:ci`

**Artifacts:**
- Backend: `htmlcov/`, `coverage.json`, `coverage.xml`
- Frontend: `frontend/coverage/`
- Retention: 30 days

### 2. Code Quality (`code-quality.yml`)

**Purpose:** Ensure code meets quality standards, follows style guides, and has proper type annotations.

**What it does:**

**Backend Quality Checks:**
1. **Black** - Code formatting (PEP 8 style)
   - Line length: 100 characters
   - Config: `pyproject.toml`

2. **isort** - Import sorting
   - Profile: black
   - Line length: 100 characters

3. **Flake8** - Linting and complexity
   - Max complexity: 10 (cyclomatic complexity)
   - Line length: 100 characters
   - Config: `pyproject.toml`

4. **mypy** - Type checking
   - Mode: strict
   - Config: `mypy.ini`
   - Python version: 3.13

**Frontend Quality Checks:**
1. **ESLint** - Code quality and linting
   - React Hooks rules
   - React Refresh rules
   - Zero warnings allowed in CI (`--max-warnings 0`)

2. **TypeScript** - Type checking
   - Command: `npm run type-check`
   - Config: `tsconfig.json`

3. **npm audit** - Security vulnerability scanning
   - Level: moderate
   - Fails on vulnerabilities

**Quality Gates:**
- All checks must pass for workflow to succeed
- Individual tool failures provide detailed error messages
- Combined summary shows overall quality status

### 3. Accessibility (`accessibility.yml`)

**Purpose:** Ensure the application meets WCAG 2.1 Level AA accessibility standards.

**What it does:**

**pa11y Tests:**
- Standard: WCAG 2.1 Level AA
- Tool: pa11y + pa11y-ci
- Tests main application pages
- Reports accessibility violations with details

**Lighthouse Audit:**
- Category: Accessibility
- Minimum score: 90/100
- Runs headless Chrome tests
- Generates detailed audit reports

**Test Process:**
1. Build production frontend (`npm run build`)
2. Start preview server (`npm run preview`)
3. Run automated accessibility tests
4. Upload Lighthouse results as artifacts
5. Generate accessibility summaries

**Pages Tested:**
- Home page (`/`)
- About page (`/about`)
- (Add more pages as needed)

**Artifacts:**
- Lighthouse results JSON
- Retention: 30 days

## Running Workflows Locally

### Backend Quality Checks

```bash
# Formatting check
black --check src/ tests/

# Auto-format
black src/ tests/

# Import sorting check
isort --check-only src/ tests/

# Auto-sort imports
isort src/ tests/

# Linting
flake8 src/ tests/ --max-complexity=10

# Type checking
mypy src/ --config-file mypy.ini

# Run all backend checks
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/
```

### Backend Tests

```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-fail-under=70 -v

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Frontend Quality Checks

```bash
cd frontend

# Linting
npm run lint:ci

# Type checking
npm run type-check

# Security audit
npm audit --audit-level=moderate
```

### Frontend Tests

```bash
cd frontend

# Run tests with coverage
npm run test:ci

# View coverage report
open coverage/index.html
```

### Accessibility Tests

```bash
cd frontend

# Build frontend
npm run build

# Start preview server
npm run preview

# In another terminal, run pa11y
pa11y http://localhost:4173 --standard WCAG2AA

# Run Lighthouse
lighthouse http://localhost:4173 --only-categories=accessibility
```

## Package.json Scripts

The following npm scripts are available in `frontend/package.json` for CI/CD:

```json
{
  "test:ci": "vitest run --coverage",
  "lint:ci": "eslint . --max-warnings 0",
  "type-check": "tsc --noEmit --skipLibCheck"
}
```

## Quality Thresholds

| Metric | Threshold | Tool | Enforcement |
|--------|-----------|------|-------------|
| Backend Coverage | ≥70% | pytest-cov | Hard fail |
| Frontend Coverage | ≥70% | Vitest | Hard fail |
| Code Complexity | ≤10 | Flake8 | Hard fail |
| Type Coverage | 100% | mypy (strict) | Hard fail |
| ESLint Warnings | 0 | ESLint | Hard fail |
| Accessibility Score | ≥90 | Lighthouse | Hard fail |
| WCAG Compliance | Level AA | pa11y | Hard fail |

## Workflow Status Badges

Add these badges to your README.md to show workflow status:

```markdown
[![Test Coverage](https://github.com/USERNAME/tkr-docusearch/actions/workflows/test-coverage.yml/badge.svg)](https://github.com/USERNAME/tkr-docusearch/actions/workflows/test-coverage.yml)
[![Code Quality](https://github.com/USERNAME/tkr-docusearch/actions/workflows/code-quality.yml/badge.svg)](https://github.com/USERNAME/tkr-docusearch/actions/workflows/code-quality.yml)
[![Accessibility](https://github.com/USERNAME/tkr-docusearch/actions/workflows/accessibility.yml/badge.svg)](https://github.com/USERNAME/tkr-docusearch/actions/workflows/accessibility.yml)
```

## Pre-commit Hooks

The project uses pre-commit hooks (`.pre-commit-config.yaml`) to catch issues before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

The pre-commit hooks run the same quality checks as CI/CD, ensuring fast feedback during development.

## Troubleshooting

### Workflow Fails on Formatting

**Solution:** Run formatters locally:
```bash
# Backend
black src/ tests/
isort src/ tests/

# Frontend
cd frontend
npm run lint -- --fix
```

### Coverage Below Threshold

**Solution:** Add more tests to increase coverage:
- Focus on untested files (check coverage reports)
- Aim for meaningful tests, not just coverage percentage
- Review `htmlcov/index.html` (backend) or `coverage/index.html` (frontend)

### Type Checking Errors

**Backend Solution:**
- Add type annotations to functions
- Use `# type: ignore` sparingly for third-party library issues
- Consult `mypy.ini` for configuration

**Frontend Solution:**
- Add JSDoc comments with type information
- Fix TypeScript errors in `.ts` and `.tsx` files
- Use `// @ts-ignore` sparingly

### Accessibility Issues

**Solution:**
- Review pa11y and Lighthouse reports
- Common fixes:
  - Add alt text to images
  - Ensure proper heading hierarchy
  - Add ARIA labels to interactive elements
  - Maintain sufficient color contrast
  - Ensure keyboard navigation works

### Security Vulnerabilities

**Solution:**
```bash
cd frontend

# Attempt automatic fix
npm audit fix

# If that doesn't work, update specific packages
npm update [package-name]

# For breaking changes, review and update manually
```

## Maintenance

### Updating Dependencies

Workflow dependencies (GitHub Actions) are managed in each workflow file:
- `actions/checkout@v4` - Code checkout
- `actions/setup-python@v5` - Python setup
- `actions/setup-node@v4` - Node.js setup
- `actions/upload-artifact@v4` - Artifact upload
- `actions/download-artifact@v4` - Artifact download

Update versions as needed when new releases are available.

### Adding New Tests

When adding new test files:
1. Backend: Add to `tests/` directory
2. Frontend: Add `.test.jsx`, `.test.tsx`, or `.spec.js` files
3. Tests are automatically discovered and run

### Modifying Thresholds

To change coverage or quality thresholds:

**Backend Coverage:**
- Edit `pyproject.toml`: `[tool.pytest.ini_options]` → `--cov-fail-under=XX`
- Update workflow: `.github/workflows/test-coverage.yml`

**Frontend Coverage:**
- Edit `frontend/vitest.config.js`: `coverage.thresholds`
- Update workflow: `.github/workflows/test-coverage.yml`

**Code Complexity:**
- Edit `pyproject.toml`: `[tool.flake8]` → `max-complexity = XX`
- Update workflow: `.github/workflows/code-quality.yml`

**Accessibility:**
- Edit workflow: `.github/workflows/accessibility.yml`
- Adjust Lighthouse threshold in workflow

## Best Practices

1. **Run checks locally before pushing:**
   - Saves CI/CD time
   - Faster feedback loop
   - Use pre-commit hooks

2. **Write meaningful tests:**
   - Don't just chase coverage numbers
   - Test behavior, not implementation
   - Include edge cases

3. **Keep dependencies updated:**
   - Run `npm audit` regularly
   - Update Python packages in `requirements.txt`
   - Monitor Dependabot alerts

4. **Review workflow outputs:**
   - Check job summaries for details
   - Download artifacts for deeper analysis
   - Fix issues promptly

5. **Accessibility is not optional:**
   - Design with accessibility in mind
   - Test with screen readers
   - Use semantic HTML

## Related Documentation

- [Contributing Guide](../../docs/CONTRIBUTING.md)
- [Testing Guide](../../docs/TESTING.md)
- [Style Guide](../../docs/STYLE_GUIDE.md)
- [Pre-commit Hooks](../../.pre-commit-config.yaml)

## Support

For questions or issues with CI/CD workflows:
1. Check workflow run logs for detailed error messages
2. Review this README and related documentation
3. Open an issue with workflow run details
