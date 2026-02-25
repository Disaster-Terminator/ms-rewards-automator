"""Test WebSocket connectivity using only stdlib"""
import socket
import hashlib
import base64
import os

def test_ws(host, port, path="/ws"):
    """Minimal WebSocket handshake test"""
    label = f"ws://{host}:{port}{path}"
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, port))
        
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            f"\r\n"
        )
        sock.send(request.encode())
        response = sock.recv(4096).decode()
        sock.close()
        
        if "101" in response:
            print(f"[OK] {label} -> WebSocket handshake successful!")
        else:
            status_line = response.split("\r\n")[0]
            print(f"[FAIL] {label} -> {status_line}")
            if "HTTP" in response:
                headers = response.split('\r\n\r\n')[0]
                print(f"  Headers: {headers}")
    except Exception as e:
        print(f"[FAIL] {label} -> {e}")

print("=== Testing WebSocket Connectivity ===\n")

# Test 1: Direct to backend
test_ws("localhost", 8000, "/ws")

# Test 2: Through Vite proxy
test_ws("localhost", 5174, "/ws")

print("\nDone.")
