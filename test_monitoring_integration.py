#!/usr/bin/env python3
"""
Integration test for real-time monitoring system.

Tests:
1. WebSocket connection
2. Document processing with real-time updates
3. Status broadcasts
4. Log broadcasts
"""

import asyncio
import websockets
import json
import sys
import requests
from pathlib import Path


class MonitoringTester:
    """Test client for monitoring system."""

    def __init__(self):
        self.messages = []
        self.status_updates = []
        self.log_messages = []
        self.websocket = None

    async def connect_websocket(self):
        """Connect to WebSocket endpoint."""
        uri = "ws://localhost:8002/ws"
        print(f"Connecting to {uri}...")
        self.websocket = await websockets.connect(uri)
        print("✓ Connected!")

    async def listen_for_messages(self, duration=30):
        """Listen for messages for specified duration."""
        print(f"Listening for messages (max {duration}s)...")
        try:
            while True:
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=duration
                )
                data = json.loads(message)
                self.messages.append(data)

                # Categorize messages
                if data.get("type") == "status_update":
                    self.status_updates.append(data)
                    print(f"  Status: {data.get('status')} - {data.get('stage')} "
                          f"({data.get('progress', 0) * 100:.0f}%)")
                elif data.get("type") == "log":
                    self.log_messages.append(data)
                    print(f"  Log [{data.get('level')}]: {data.get('message')}")
                elif data.get("type") == "connection":
                    print(f"  Connection: {data.get('message')}")

        except asyncio.TimeoutError:
            print(f"✓ Listening completed (timeout)")

    def submit_document(self, file_path):
        """Submit a document for processing."""
        print(f"\nSubmitting document: {file_path}")

        payload = {
            "file_path": str(file_path),
            "filename": file_path.name
        }

        response = requests.post(
            "http://localhost:8002/process",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Document queued: {data.get('doc_id')}")
            return data.get('doc_id')
        else:
            print(f"✗ Failed to submit: {response.status_code}")
            print(f"  {response.text}")
            return None

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Total messages: {len(self.messages)}")
        print(f"Status updates: {len(self.status_updates)}")
        print(f"Log messages: {len(self.log_messages)}")
        print()

        if self.status_updates:
            print("Status progression:")
            for update in self.status_updates:
                print(f"  - {update.get('status'):12} | "
                      f"{update.get('stage'):20} | "
                      f"{update.get('progress', 0) * 100:5.1f}%")
            print()

        if self.log_messages:
            print(f"Log levels: {set(msg.get('level') for msg in self.log_messages)}")
            print()

        # Verify we got expected messages
        has_started = any(u.get('stage') == 'started' for u in self.status_updates)
        has_completed = any(u.get('status') == 'completed' for u in self.status_updates)

        print("Verification:")
        print(f"  {'✓' if has_started else '✗'} Received start message")
        print(f"  {'✓' if has_completed else '✗'} Received completion message")
        print()

        return has_started and has_completed


async def main():
    """Run monitoring integration test."""
    print("=" * 60)
    print("Real-Time Monitoring Integration Test")
    print("=" * 60)
    print()

    # Find a test document
    uploads_dir = Path("data/uploads")
    test_docs = list(uploads_dir.glob("*.pdf"))

    if not test_docs:
        test_docs = list(uploads_dir.glob("*.docx"))

    if not test_docs:
        print("✗ No test documents found in data/uploads/")
        print("  Please add a PDF or DOCX file to test with")
        sys.exit(1)

    test_doc = test_docs[0]
    print(f"Test document: {test_doc.name}")
    print()

    tester = MonitoringTester()

    try:
        # Connect to WebSocket
        await tester.connect_websocket()

        # Start listening task
        listen_task = asyncio.create_task(tester.listen_for_messages(duration=30))

        # Wait a moment for connection to be established
        await asyncio.sleep(1)

        # Submit document
        doc_id = tester.submit_document(test_doc)

        if not doc_id:
            print("✗ Failed to submit document")
            listen_task.cancel()
            sys.exit(1)

        # Wait for processing to complete
        await listen_task

        # Print summary
        success = tester.print_summary()

        if success:
            print("✓ All monitoring features working!")
            print()
            print("You can now open the monitor UI in your browser:")
            print("  → http://localhost:8002/static/monitor.html")
            print()
            print("Upload a document at:")
            print("  → http://localhost:8000")
            sys.exit(0)
        else:
            print("✗ Some features not working as expected")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if tester.websocket:
            await tester.websocket.close()


if __name__ == "__main__":
    asyncio.run(main())
