#!/usr/bin/env python3
"""
Simple WebSocket test client to verify monitoring system.

Tests:
1. WebSocket connection
2. Receiving welcome message
3. Connection management
"""

import asyncio
import json
import sys

import websockets


async def test_websocket_connection():
    """Test WebSocket connection and message reception."""
    uri = "ws://localhost:8002/ws"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully!")

            # Wait for welcome message
            print("Waiting for welcome message...")
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)

            print(f"✓ Received message: {json.dumps(data, indent=2)}")

            # Verify it's a connection message
            if data.get("type") == "connection" and data.get("status") == "connected":
                print("✓ Welcome message verified!")
                return True
            else:
                print("✗ Unexpected message type")
                return False

    except asyncio.TimeoutError:
        print("✗ Timeout waiting for message")
        return False
    except websockets.exceptions.WebSocketException as e:
        print(f"✗ WebSocket error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


async def main():
    """Run WebSocket tests."""
    print("=" * 60)
    print("WebSocket Monitoring Test")
    print("=" * 60)
    print()

    success = await test_websocket_connection()

    print()
    print("=" * 60)
    if success:
        print("✓ All tests passed!")
        print()
        print("You can now open the monitor UI in your browser:")
        print("  → http://localhost:8002/static/monitor.html")
        sys.exit(0)
    else:
        print("✗ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
