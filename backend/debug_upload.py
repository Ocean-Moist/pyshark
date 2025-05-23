#!/usr/bin/env python3
import requests
import os

# Test the upload endpoint directly
pcap_file = "../ue0.pcap"

if not os.path.exists(pcap_file):
    print(f"File not found: {pcap_file}")
    exit(1)

print(f"File size: {os.path.getsize(pcap_file)} bytes")

url = "http://localhost:8000/upload"

with open(pcap_file, "rb") as f:
    files = {"file": (os.path.basename(pcap_file), f, "application/octet-stream")}
    response = requests.post(url, files=files)

print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code != 200:
    # Try to get more info
    import json
    try:
        error_detail = json.loads(response.text)
        print(f"Error detail: {error_detail}")
    except:
        pass