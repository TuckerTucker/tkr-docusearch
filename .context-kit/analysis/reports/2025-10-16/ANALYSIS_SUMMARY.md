# Code Quality Analysis Summary

**Project:** tkr-docusearch  
**Analysis Date:** 2025-10-16  
**Files Analyzed:** 70 Python modules  
**Total LOC:** 24,306

## Overall Quality Score: 73/100 (Good - Maintainable)

### Severity Breakdown

- **Critical Issues:** 3 (Complexity F/D rank)
- **Major Issues:** 27 (Complexity C-D rank + large files)
- **Minor Issues:** 247 (PEP 8 violations, unused imports)
- **Technical Debt:** 8 TODO/FIXME comments

---

## Top Priority Fixes

### 1. CRITICAL: DoclingParser._parse_with_docling (CC: 57, Rank F)
**Location:** `src/processing/docling_parser.py:460`  
**Issue:** Extremely high cyclomatic complexity (57 decision points)  
**Impact:** Nearly impossible to test, high risk of bugs  
**Recommendation:**
- Extract document type handlers: `PdfParseStrategy`, `DocxParseStrategy`, `PptxParseStrategy`
- Create `AsrOptionsBuilder` for ASR configuration
- Apply Strategy pattern with factory
- Target complexity: < 10 per method

### 2. CRITICAL: DocumentProcessor._store_embeddings (CC: 29, Rank D)
**Location:** `src/processing/processor.py:483`  
**Issue:** Very high complexity with multiple nested conditionals  
**Impact:** Core processing logic with high bug risk  
**Recommendation:**
- Extract `VisualEmbeddingHandler` and `TextEmbeddingHandler` classes
- Use early returns to reduce nesting
- Apply Command pattern for embedding types

### 3. CRITICAL: docling_to_pages (CC: 29, Rank D)
**Location:** `src/processing/docling_parser.py:121`  
**Issue:** Complex page conversion logic  
**Recommendation:**
- Break into smaller functions: `_extract_page_metadata()`, `_process_page_images()`, `_build_page_object()`
- Consider Builder pattern for Page construction

---

## Complexity Hotspots (CC > 10)

| Function | File | Line | CC | Rank |
|----------|------|------|----|----|
| DoclingParser._parse_with_docling | docling_parser.py | 460 | 57 | F |
| docling_to_pages | docling_parser.py | 121 | 29 | D |
| DocumentProcessor._store_embeddings | processor.py | 483 | 29 | D |
| get_document | documents_api.py | 363 | 28 | D |
| DocumentProcessor.process_document | processor.py | 129 | 27 | D |
| verify_output_shapes | verify_implementation.py | 95 | 23 | D |
| validate_embedding_interface | validate_mocks.py | 29 | 22 | D |
| AudioMetadata (class) | audio_metadata.py | 27 | 21 | D |
| AudioMetadata.to_chromadb_metadata | audio_metadata.py | 56 | 20 | C |
| _extract_tables | structure_extractor.py | 160 | 20 | C |

**Total functions with CC > 10:** 30

---

## Large Files (>500 LOC)

| File | LOC | MI | Status |
|------|-----|-------|--------|
| docling_parser.py | 1,017 | 29.4 | Review - Split recommended |
| documents_api.py | 981 | 34.9 | Review - Split recommended |
| chroma_client.py | 912 | 41.0 | Review - Extract operations |
| test_storage.py | 872 | 28.2 | Test file - Acceptable |
| worker_webhook.py | 746 | 45.2 | Review - Separate handlers |
| processor.py | 741 | 41.4 | Review - Extract handlers |
| test_processing.py | 654 | 24.4 | Test file - Acceptable |
| test_search.py | 578 | 26.4 | Test file - Acceptable |
| processing_config.py | 545 | 53.7 | OK |

---

## PEP 8 Compliance

**Total Violations:** 247

### Breakdown by Type

| Violation | Count | Description |
|-----------|-------|-------------|
| F401 | 104 | Unused imports |
| E501 | 60 | Line too long (>100 chars) |
| F541 | 33 | f-string missing placeholders |
| E402 | 27 | Import not at top of file |
| F841 | 10 | Unused variables |
| F811 | 5 | Redefinition of unused name |
| E722 | 1 | Bare except (CRITICAL) |
| E712 | 4 | Comparison to True |

### Critical PEP 8 Issues

**Bare Except Clause (E722):**
- Location: `src/embeddings/model_loader.py:366`
- Danger: Catches all exceptions including SystemExit and KeyboardInterrupt
- Fix: Replace with `except Exception as e:` or specific exception types

---

## Code Smells

### TODO/FIXME Comments (8 found)

| File | Line | Comment |
|------|------|---------|
| test_audio_album_art.py | 276, 290, 303, 316, 329, 354 | TODO: Implement once full processing pipeline is integrated (6x) |
| smart_chunker.py | 46 | TODO: Could be made configurable to match text embedding model |
| server.py | 440 | TODO: Implement actual status tracking |

**Recommendation:** Convert to GitHub issues for proper tracking.

### Potential Duplication Areas

- **Test files:** Common setup patterns could be extracted to `conftest.py` fixtures
- **API handlers:** Error handling patterns repeated across `documents_api.py` endpoints  
- **Metadata extraction:** Similar patterns in `audio_metadata.py` and `structure_extractor.py`

---

## Maintainability Index

**Average MI:** 63.2 (Rank A)  
**Range:** 24.2 - 100.0  
**All files:** Rank A

### Files with MI < 40 (Non-Test)

| File | MI | Primary Issues |
|------|-----|----------------|
| docling_parser.py | 29.4 | High complexity (F57), long file (1017 LOC) |
| documents_api.py | 34.9 | High complexity (D28), long file (981 LOC) |
| verify_implementation.py | 37.5 | High complexity (D23) |

---

## Type Safety

**Status:** EXCELLENT ✓

- No explicit `any` types found
- No unsafe type casts detected
- Extensive use of Pydantic models
- Good use of dataclasses and type hints
- No wildcard imports

**Recommendation:** Run `mypy src/ --strict` for comprehensive type checking

---

## Strengths

1. **Excellent type safety** - Extensive use of Pydantic models and type hints
2. **Comprehensive test coverage** - Test files account for significant LOC
3. **Good modern Python patterns** - Dataclasses, type hints, async/await
4. **All files Rank A** - No files in critical MI range
5. **No unsafe patterns** - No wildcard imports or unsafe type casts

---

## Action Plan

### Week 1: Critical Refactoring
- [ ] Refactor `DoclingParser._parse_with_docling` (CC: 57 → <10)
- [ ] Fix bare except in `model_loader.py:366`
- [ ] Add complexity guards to CI/CD

### Week 2: High Complexity Functions
- [ ] Refactor `DocumentProcessor._store_embeddings` (CC: 29 → <10)
- [ ] Refactor `DocumentProcessor.process_document` (CC: 27 → <10)
- [ ] Refactor `get_document` in documents_api.py (CC: 28 → <10)

### Week 3: File Organization
- [ ] Split `docling_parser.py` (1017 LOC) into separate handlers
- [ ] Split `documents_api.py` (981 LOC) into separate routers
- [ ] Extract collection operations from `chroma_client.py` (912 LOC)

### Week 4: Code Hygiene
- [ ] Remove unused imports: `autoflake --remove-all-unused-imports --in-place --recursive src/`
- [ ] Fix line length: `black src/ --line-length 100`
- [ ] Organize imports: `isort src/`
- [ ] Convert TODOs to GitHub issues

### Ongoing: Automation
- [ ] Add pre-commit hooks (flake8, black, isort, pylint)
- [ ] Configure complexity gates (max CC: 10)
- [ ] Add radon to CI/CD pipeline
- [ ] Set up automated code quality reports

---

## Automation Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --max-complexity=10]

  - repo: https://github.com/psf/black
    rev: 24.0.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: local
    hooks:
      - id: radon-cc
        name: Radon Complexity Check
        entry: radon cc --min C src/
        language: system
        pass_filenames: false
```

---

## Quick Fixes (Can be automated)

```bash
# Remove unused imports
autoflake --remove-all-unused-imports --in-place --recursive src/

# Fix line length and formatting
black src/ --line-length 100

# Organize imports
isort src/ --profile black

# Check complexity
radon cc src/ -a -s -n C

# Run type checking
mypy src/ --strict
```

---

## Full Report

Complete HTML report with interactive visualizations:  
`/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/.context-kit/analysis/reports/2025-10-16/code-quality-report.html`

---

**Generated by:** Code Quality Agent (tkr-context-kit v3.6.0)  
**Tools Used:** radon, flake8, custom pattern analysis  
**Analysis Duration:** ~5 minutes
