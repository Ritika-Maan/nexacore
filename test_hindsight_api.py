#!/usr/bin/env python3
"""
Quick script to test Hindsight API connectivity and endpoints.
Usage: python test_hindsight_api.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").rstrip("/")
API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
PROJECT = os.getenv("HINDSIGHT_PROJECT", "ramp-onboarding-demo")

print(f"Testing Hindsight API: {BASE_URL}")
print(f"API Key: {'*' * (len(API_KEY) - 4)}{API_KEY[-4:] if len(API_KEY) > 4 else '(not set)'}")
print(f"Project: {PROJECT}")
print("-" * 60)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# Test endpoints
endpoints_to_test = [
    ("GET", "/health", None),
    ("GET", "/", None),
    ("GET", "/namespaces", None),
    ("POST", "/search", {"tags": [], "query": "", "limit": 1}),
    ("POST", "/records", {
        "id": "test-record-123",
        "content": "Test memory content",
        "tags": ["test"],
        "namespace": "test",
        "level": "team",
        "source": "api-test"
    }),
]

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
            try:
                data = response.json()
                print(f"  Response: {data}")
            except:
                print(f"  Response (text): {response.text[:200]}")
        else:
            print(f"  Error: {response.text[:200]}")
    except requests.exceptions.ConnectionError as e:
        print(f"  ❌ Connection Error: {e}")
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("Summary:")
print("If you see 404 errors, the Hindsight API may not be available yet.")
print("The application will automatically fall back to local storage.")
print("=" * 60)
