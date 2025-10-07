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

### Search Documents

```bash
# Simple text search in stored text chunks
./scripts/query-chromadb.sh --search "revenue"

# Show more results
./scripts/query-chromadb.sh --search "quarterly" --top-k 10
```

**Note:** Text search only works if text embeddings are stored. Currently, the system stores visual embeddings only.

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
- Text search requires text embeddings to be stored
- Use `--list-docs` to see what documents exist
