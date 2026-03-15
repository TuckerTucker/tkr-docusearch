# PDF Dimension Repair

DocuSearch automatically repairs PDFs with missing page dimensions before Docling processing.

## Problem

Some PDFs lack explicit MediaBox/CropBox on individual page objects, inheriting dimensions from the parent page tree instead. While PDF viewers handle this correctly, Docling requires explicit dimensions on each page.

This commonly occurs with:
- PDFs from certain generators or optimization tools
- PDFs with uniform page sizes
- Legacy PDF files

## How It Works

The repair is **automatic and transparent**. Before sending any PDF to Docling, the system:

1. Checks each page for MediaBox/CropBox
2. If missing, resolves dimensions from the parent page tree via `pypdf`
3. Writes explicit dimensions to each page object
4. Continues normal processing

## Detection

Check the worker logs:

```bash
tail -50 logs/worker-native.log | grep -i "dimension"
```

Look for:
```
INFO - PDF missing explicit page dimensions, repairing with pypdf...
INFO - Successfully repaired PDF dimensions
```

## Performance Impact

| PDF Size | Overhead |
|----------|----------|
| < 10 pages | ~50-200ms |
| 100+ pages | ~500ms-1s |

Only runs when needed — the dimension check itself is very fast.

## Edge Cases

| Scenario | Supported |
|----------|-----------|
| Missing dimensions on all pages | Yes |
| Inherited from parent node | Yes |
| Completely missing dimension info | No (invalid PDF) |
| Encrypted PDFs | Must be decrypted first |
| Corrupted page tree | No (requires manual repair) |

## Dependencies

- `pypdf>=3.0.0` — PDF structure manipulation
- `docling` — document processing (benefits from repair)

## Source

- Implementation: `src/processing/docling_parser.py`
- Tests: `tests/processing/test_pdf_repair_manual.py`
