#!/usr/bin/env python3
"""
Test QoS extraction from PCAP
"""

import requests
import json

API_BASE = "http://localhost:8000"
PCAP_FILE = "../ue0.pcap"

def test_qos_extraction():
    print("🧪 Testing QoS Extraction\n")
    
    # 1. Upload PCAP
    print("📤 Uploading PCAP...")
    with open(PCAP_FILE, 'rb') as f:
        files = {'file': f}
        r = requests.post(f"{API_BASE}/upload", files=files)
        
    if r.status_code != 200:
        print(f"❌ Upload failed: {r.text}")
        return
        
    upload_result = r.json()
    file_id = upload_result['file_id']
    print(f"✅ Uploaded: {upload_result['filename']} ({upload_result['packet_count']} packets)\n")
    
    # 2. Query for QoS
    queries = [
        "Extract the UL and DL QoS parameters and present them in a table format",
        "What are the QFI values and their associated 5QI/QoS characteristics?",
        "Show me the guaranteed bit rates (GBR) and maximum bit rates (MBR) for uplink and downlink",
        "Are there any QoS flows configured? What are their priorities?"
    ]
    
    messages = []
    
    for query in queries:
        print(f"\n{'='*80}")
        print(f"🤔 Query: {query}")
        print(f"{'='*80}\n")
        
        messages.append({"role": "user", "content": query})
        
        payload = {
            "messages": messages.copy(),
            "file_id": file_id
        }
        
        r = requests.post(f"{API_BASE}/analyze", json=payload)
        
        if r.status_code != 200:
            print(f"❌ Analysis failed: {r.text}")
            continue
            
        result = r.json()
        response = result['response']
        
        print(f"📝 Response:\n{response}")
        
        messages.append({"role": "assistant", "content": response})
        
        # Only do first query for now
        break

if __name__ == "__main__":
    test_qos_extraction()