#!/usr/bin/env python3
"""
Quick script to test Hindsight API connectivity and endpoints.
Usage: python test_hindsight_api.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "http://localhost:8888").rstrip("/")
API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
PROJECT = os.getenv("HINDSIGHT_PROJECT", "ramp-onboarding-demo")

print(f"Testing Hindsight API: {BASE_URL}")
print(f"API Key: {'*' * max(0, len(API_KEY) - 4)}{API_KEY[-4:] if len(API_KEY) > 4 else '(not set)'}")
print(f"Project/Bank ID: {PROJECT}")
print("-" * 60)

headers = {
    "Content-Type": "application/json",
}
if API_KEY:
    headers["Authorization"] = f"Bearer {API_KEY}"

# Test endpoints with correct v1 API structure
endpoints_to_test = [
    ("GET", "/health", None),
    ("POST", f"/v1/default/banks/{PROJECT}/memories/recall", {
        "query": "test search",
        "top_k": 5
    }),
    ("POST", f"/v1/default/banks/{PROJECT}/memories/retain", {
        "content": "Test memory for API verification",
        "tags": ["test", "api-verification"],
        "metadata": {
            "source": "api-test",
            "namespace": "test"
        }
    }),
    ("GET", f"/v1/default/banks/{PROJECT}/memories/list", None),
]

success_count = 0
for method, path, payload in endpoints_to_test:
    url = BASE_URL + path
    print(f"\n{method} {path}")
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        print(f"  Status: {response.status_code}")
        if response.status_code < 400:
            success_count += 1
            try:
                data = response.json()
                print(f"  ✅ Success: {str(data)[:150]}")
            except:
                print(f"  ✅ Success (text): {response.text[:150]}")
        else:
            print(f"  ❌ Error: {response.text[:200]}")
    except requests.exceptions.ConnectionError as e:
        print(f"  ❌ Connection Error: {e}")
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print(f"Results: {success_count}/{len(endpoints_to_test)} endpoints working")
print("=" * 60)

if success_count == 0:
    print("\n⚠️  Hindsight service not reachable!")
    print("Make sure it's running:")
    print("  docker run -p 8888:8888 -e HINDSIGHT_API_LLM_API_KEY=<key> \\")
    print("    -v hindsight-data:/home/hindsight/.pg0 \\")
    print("    ghcr.io/vectorize-io/hindsight:latest")
elif success_count < len(endpoints_to_test):
    print("\n⚠️  Some endpoints failed. Check Hindsight logs.")
else:
    print("\n✅ All endpoints working! Hindsight is properly configured.")
    print("\nYou can now set in your .env:")
    print(f"  HINDSIGHT_BACKEND=http")
    print(f"  HINDSIGHT_BASE_URL={BASE_URL}")
    print(f"  HINDSIGHT_PROJECT={PROJECT}")

print("=" * 60)
