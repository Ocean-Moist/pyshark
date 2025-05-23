#!/usr/bin/env python3
"""
Quick test to verify the analyzer is working with o4-mini
"""

import requests
import json
import os

API_BASE = "http://localhost:8000"
PCAP_FILE = "../ue0.pcap"

def test_analyzer():
    print("🧪 Quick Test - 5G Callflow Analyzer with o4-mini\n")
    
    # 1. Check API is running
    try:
        r = requests.get(f"{API_BASE}/")
        print(f"✅ API is running: {r.json()}")
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        print("Please start the backend: cd backend && uvicorn main:app --reload")
        return
        
    # 2. Upload PCAP
    print(f"\n📤 Uploading {PCAP_FILE}...")
    with open(PCAP_FILE, 'rb') as f:
        files = {'file': f}
        r = requests.post(f"{API_BASE}/upload", files=files)
        
    if r.status_code != 200:
        print(f"❌ Upload failed: {r.text}")
        return
        
    upload_result = r.json()
    file_id = upload_result['file_id']
    print(f"✅ Uploaded: {upload_result['filename']} ({upload_result['packet_count']} packets)")
    
    # 3. Test query
    query = "What type of 5G procedures are in this PCAP file? List the main message types."
    print(f"\n🤔 Query: {query}")
    
    payload = {
        "messages": [{"role": "user", "content": query}],
        "file_id": file_id
    }
    
    print("\n⏳ Analyzing with o4-mini...")
    r = requests.post(f"{API_BASE}/analyze", json=payload)
    
    if r.status_code != 200:
        print(f"❌ Analysis failed: {r.text}")
        return
        
    result = r.json()
    model = result.get('model_used', 'unknown')
    response = result['response']
    
    print(f"\n🤖 Model used: {model}")
    print(f"\n📝 Response:\n{response}")
    
    # 4. Follow-up query
    query2 = "Focus on the registration procedure - what are the key steps?"
    print(f"\n\n🤔 Follow-up: {query2}")
    
    payload['messages'].append({"role": "assistant", "content": response})
    payload['messages'].append({"role": "user", "content": query2})
    
    r = requests.post(f"{API_BASE}/analyze", json=payload)
    if r.status_code == 200:
        result2 = r.json()
        print(f"\n📝 Response:\n{result2['response']}")
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    test_analyzer()