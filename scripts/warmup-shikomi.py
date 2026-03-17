#!/usr/bin/env python3
"""Send a warmup request to Shikomi to trigger model loading.

This forces the embedding model to load at startup rather than on
first document upload, avoiding a long wait for the first user.

Runs as a background process so it doesn't block the rest of startup.
"""

import os
import sys

def main() -> int:
    target = os.getenv("SHIKOMI_GRPC_TARGET", "localhost:50051")

    try:
        import grpc
    except ImportError:
        print("  ⚠ grpc not installed, skipping warmup")
        return 1

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, project_root)

    try:
        from src.embeddings.proto import embedding_pb2, embedding_pb2_grpc
    except ImportError:
        print("  ⚠ Proto imports failed, skipping warmup")
        return 1

    print(f"  ℹ Warming up Shikomi at {target} (loading model)...")
    sys.stdout.flush()

    max_msg = 100 * 1024 * 1024
    options = [
        ("grpc.max_send_message_length", max_msg),
        ("grpc.max_receive_message_length", max_msg),
    ]
    channel = grpc.insecure_channel(target, options=options)
    stub = embedding_pb2_grpc.EmbeddingServiceStub(channel)

    try:
        req = embedding_pb2.EncodeRequest(texts=["warmup"])
        resp = stub.EncodeDocuments(req, timeout=600)
        dim = 0
        if resp.embeddings:
            emb = resp.embeddings[0]
            dim = emb.dim
            tokens = emb.num_tokens
            print(f"  ✓ Shikomi model loaded (dim={dim}, tokens={tokens})")
        else:
            print("  ✓ Shikomi model loaded (no embeddings returned)")
        return 0
    except Exception as exc:
        print(f"  ⚠ Warmup failed: {exc}")
        return 1
    finally:
        channel.close()


if __name__ == "__main__":
    sys.exit(main())
