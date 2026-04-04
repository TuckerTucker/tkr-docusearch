#!/bin/bash
# batch_upload.sh — Upload audio files to DocuSearch one at a time.
#
# Uploads each file, waits for the worker to finish processing,
# then moves to the next. Skips files already in the library.
#
# Usage:
#   ./scripts/batch_upload.sh <directory> [worker_url]
#
# Requires: Bash 3.2+, curl, python3

set -euo pipefail

DIR="${1:?Usage: $0 <directory> [worker_url]}"
WORKER_URL="${2:-http://localhost:8002}"
POLL_INTERVAL=5
TIMEOUT=900          # 15 min per file (large audio can be slow)

EXTENSIONS="mp3|wav|m4a|ogg|flac|aac|wma"

# Collect audio files
FILES=()
while IFS= read -r f; do
    FILES+=("$f")
done < <(find "$DIR" -maxdepth 1 -type f | grep -iE "\.($EXTENSIONS)$" | sort)

TOTAL=${#FILES[@]}
if [ "$TOTAL" -eq 0 ]; then
    echo "No audio files found in: $DIR"
    exit 1
fi

# Fetch existing filenames from the library (paginate with limit=100)
EXISTING_FILE=$(mktemp)
trap 'rm -f "$EXISTING_FILE"' EXIT

OFFSET=0
while true; do
    PAGE=$(curl -s --max-time 10 "${WORKER_URL}/documents?limit=100&offset=${OFFSET}" 2>/dev/null || echo "")
    if [ -z "$PAGE" ]; then
        break
    fi

    # Extract filenames from JSON
    NAMES=$(echo "$PAGE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for d in data.get('documents', []):
        fn = d.get('filename', '')
        if fn:
            print(fn)
except Exception:
    pass
" 2>/dev/null || echo "")

    if [ -z "$NAMES" ]; then
        break
    fi

    echo "$NAMES" >> "$EXISTING_FILE"
    COUNT=$(echo "$NAMES" | wc -l | tr -d ' ')
    OFFSET=$((OFFSET + COUNT))
done

EXISTING_COUNT=$(wc -l < "$EXISTING_FILE" | tr -d ' ')

echo "=== DocuSearch Batch Upload ==="
echo "Directory: $DIR"
echo "Files:     $TOTAL"
echo "Existing:  $EXISTING_COUNT (will skip)"
echo "Worker:    $WORKER_URL"
echo ""

OK_COUNT=0
ERR_COUNT=0
SKIP_COUNT=0

wait_for_processing() {
    local doc_id="$1"
    local elapsed=0

    while [ "$elapsed" -lt "$TIMEOUT" ]; do
        local status_resp
        status_resp=$(curl -s --max-time 5 "${WORKER_URL}/status/${doc_id}" 2>/dev/null || echo '{}')

        local status
        status=$(echo "$status_resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")

        case "$status" in
            completed)
                return 0
                ;;
            failed)
                local err
                err=$(echo "$status_resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error','unknown error'))" 2>/dev/null || echo "unknown")
                echo "FAILED: ${err}"
                return 1
                ;;
            *)
                sleep "$POLL_INTERVAL"
                elapsed=$((elapsed + POLL_INTERVAL))
                ;;
        esac
    done

    echo "TIMEOUT after ${TIMEOUT}s"
    return 1
}

for filepath in "${FILES[@]}"; do
    INDEX=$((OK_COUNT + ERR_COUNT + SKIP_COUNT + 1))
    filename=$(basename "$filepath")

    # Skip if already in library
    if grep -qx "$filename" "$EXISTING_FILE" 2>/dev/null; then
        echo "[${INDEX}/${TOTAL}] SKIP ${filename} (already in library)"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    # Skip files over 100MB (worker upload limit)
    file_size=$(stat -f%z "$filepath" 2>/dev/null || echo 0)
    max_bytes=$((100 * 1024 * 1024))
    if [ "$file_size" -gt "$max_bytes" ]; then
        size_mb=$(( file_size / 1024 / 1024 ))
        echo "[${INDEX}/${TOTAL}] SKIP ${filename} (${size_mb}MB > 100MB limit)"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    # Upload
    resp=$(curl -s --max-time 300 -w "\n%{http_code}" -X POST "${WORKER_URL}/uploads/" \
        -F "f=@${filepath}" 2>&1)

    http_code=$(echo "$resp" | tail -1)
    body=$(echo "$resp" | sed '$d')

    if [ "$http_code" != "200" ]; then
        echo "[${INDEX}/${TOTAL}] UPLOAD_ERR ${filename} (HTTP ${http_code})"
        ERR_COUNT=$((ERR_COUNT + 1))
        continue
    fi

    doc_id=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('doc_id',''))" 2>/dev/null || echo "")

    if [ -z "$doc_id" ]; then
        echo "[${INDEX}/${TOTAL}] UPLOAD_ERR ${filename} (no doc_id)"
        ERR_COUNT=$((ERR_COUNT + 1))
        continue
    fi

    printf "[%d/%d] %-40s " "$INDEX" "$TOTAL" "$filename"

    if wait_for_processing "$doc_id"; then
        echo "OK"
        OK_COUNT=$((OK_COUNT + 1))
    else
        ERR_COUNT=$((ERR_COUNT + 1))
    fi
done

echo ""
echo "=== Complete ==="
echo "Succeeded: ${OK_COUNT}"
echo "Skipped:   ${SKIP_COUNT}"
if [ "$ERR_COUNT" -gt 0 ]; then
    echo "Failed:    ${ERR_COUNT}"
fi
echo "Total:     ${TOTAL}"
