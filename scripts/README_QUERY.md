# ChromaDB Query Script

Simple utility to inspect and query the ChromaDB vector database.

## Prerequisites

- ChromaDB running at localhost:8001 (default)
- Virtual environment set up (`./scripts/run-worker-native.sh setup`)

## Usage

### Show Statistics

```bash
./scripts/query-chromadb.sh
```

**Output:**
```
📊 Collection Counts:
  Visual embeddings: 13
  Text embeddings:   0
  Total documents:   1
  Storage size:      1.30 MB
  Collections:       visual, text
```

### List All Documents

```bash
./scripts/query-chromadb.sh --list-docs
```

**Output:**
```
📄 Total documents: 1

1. Stories_Data_1755806421.pdf
   ID: de308929-186c-474c-8966-36a0542661ab
   Pages: N/A
   Source: N/A
```

### Search Documents (Semantic Similarity)

```bash
# Semantic search using ColPali embeddings (hybrid mode: visual + text)
./scripts/query-chromadb.sh --search "prompting techniques"

# Visual-only search
./scripts/query-chromadb.sh --search "revenue" --mode visual_only

# Text-only search
./scripts/query-chromadb.sh --search "quarterly" --mode text_only

# Show more results
./scripts/query-chromadb.sh --search "data science" --top-k 10
```

**How it works:**
- Uses ColPali model to generate query embeddings
- Two-stage search: fast retrieval (Stage 1) + precise re-ranking (Stage 2)
- Supports hybrid, visual-only, or text-only search modes
- Returns results ranked by semantic similarity scores

### Custom ChromaDB Instance

```bash
# Connect to different host/port
./scripts/query-chromadb.sh --host 192.168.1.100 --port 8001
```

## Help

```bash
./scripts/query-chromadb.sh --help
```

## Examples

### Check if documents were processed
```bash
# Should show > 0 visual embeddings
./scripts/query-chromadb.sh
```

### See all uploaded documents
```bash
./scripts/query-chromadb.sh --list-docs
```

### Semantic search examples
```bash
# Find documents about prompting
./scripts/query-chromadb.sh --search "prompting techniques" --top-k 3

# Expected output:
# 1. Five_7_figure_prompting_techniques_530_Penfriend_1700543858.pdf
#    Score: 0.8740

# Search for data science content
./scripts/query-chromadb.sh --search "data science stories"

# Expected output:
# 1. Stories_Data_1755806421.pdf
#    Score: 0.6764
```

### Verify specific document
```bash
./scripts/query-chromadb.sh --list-docs | grep "myfile.pdf"
```

## Troubleshooting

**"Failed to connect":**
- Ensure ChromaDB is running: `docker ps | grep chromadb`
- Check port: `curl http://localhost:8001/api/v2/version`

**"Virtual environment not found":**
- Run setup: `./scripts/run-worker-native.sh setup`

**"No matches found":**
- Try different search modes: `--mode hybrid`, `--mode visual_only`, or `--mode text_only`
- Use `--list-docs` to see what documents exist
- Try broader or more specific queries
