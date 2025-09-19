#!/usr/bin/env python3
import base64

api_key = "YzZlYTFiZmQtNmZhYy00ZTQxLTkyNWMtNDYyODQ3N2UyOTU0OnpoTXlidndIZ3JuZQ=="

try:
    decoded = base64.b64decode(api_key).decode('utf-8')
    print(f"Decoded API key: {decoded}")
    
    # Split by colon if it exists
    if ':' in decoded:
        parts = decoded.split(':')
        print(f"Part 1 (API Key): {parts[0]}")
        print(f"Part 2 (Secret): {parts[1]}")
        print(f"This looks like API_KEY:SECRET format")
    else:
        print("No colon separator found")
        
except Exception as e:
    print(f"Failed to decode: {e}")