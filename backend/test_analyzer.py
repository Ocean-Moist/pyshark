#!/usr/bin/env python3
"""
Test script for the 5G Callflow Analyzer using ue0.pcap
Tests various queries to evaluate o4-mini's analysis capabilities
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
PCAP_FILE = "../ue0.pcap"

# Test queries for 5G analysis
TEST_QUERIES = [
    "What are the main procedures in this call flow?",
    "Describe the UE registration procedure in this capture",
    "Are there any failed procedures or error messages?",
    "What NGAP messages are exchanged between the UE and the network?",
    "Explain the NAS security setup procedure",
    "What is the sequence of messages for establishing a PDU session?",
    "Identify any authentication or security procedures",
    "What are the key identifiers (UE ID, SUPI, etc.) used in this flow?",
    "Summarize the overall call flow in a step-by-step manner",
    "Are there any performance issues or delays visible in the packet timing?"
]

class CallflowAnalyzerTester:
    def __init__(self):
        self.session = None
        self.file_id = None
        self.results = []
        
    async def setup(self):
        """Initialize the aiohttp session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            
    async def upload_pcap(self) -> Dict[str, Any]:
        """Upload the PCAP file"""
        print(f"\n📤 Uploading {PCAP_FILE}...")
        
        # Check if file exists
        if not os.path.exists(PCAP_FILE):
            raise FileNotFoundError(f"PCAP file not found: {PCAP_FILE}")
            
        # Upload file
        with open(PCAP_FILE, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=os.path.basename(PCAP_FILE))
            
            async with self.session.post(f"{API_BASE_URL}/upload", data=data) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Upload failed: {error_text}")
                    
                result = await resp.json()
                self.file_id = result['file_id']
                print(f"✅ Uploaded successfully!")
                print(f"   File ID: {result['file_id']}")
                print(f"   Packets: {result['packet_count']}")
                print(f"   Size: {result['size']} bytes")
                return result
                
    async def analyze_query(self, query: str, messages: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send a query for analysis"""
        if messages is None:
            messages = []
            
        messages.append({"role": "user", "content": query})
        
        payload = {
            "messages": messages,
            "file_id": self.file_id
        }
        
        async with self.session.post(
            f"{API_BASE_URL}/analyze",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Analysis failed: {error_text}")
                
            return await resp.json()
            
    async def run_test_queries(self):
        """Run all test queries"""
        print(f"\n🧪 Running {len(TEST_QUERIES)} test queries with o4-mini...\n")
        
        messages = []  # Maintain conversation context
        
        for i, query in enumerate(TEST_QUERIES, 1):
            print(f"\n{'='*80}")
            print(f"Query {i}/{len(TEST_QUERIES)}: {query}")
            print(f"{'='*80}")
            
            start_time = datetime.now()
            
            try:
                result = await self.analyze_query(query, messages.copy())
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                response = result['response']
                model_used = result.get('model_used', 'unknown')
                
                print(f"\n🤖 Model: {model_used}")
                print(f"⏱️  Response time: {duration:.2f}s")
                print(f"\n📝 Response:\n{response}")
                
                # Add to conversation history
                messages.append({"role": "user", "content": query})
                messages.append({"role": "assistant", "content": response})
                
                # Store result
                self.results.append({
                    "query": query,
                    "response": response,
                    "model": model_used,
                    "duration": duration,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                self.results.append({
                    "query": query,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                
            # Small delay between queries
            await asyncio.sleep(1)
            
    def save_results(self):
        """Save test results to file"""
        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                "test_date": datetime.now().isoformat(),
                "pcap_file": PCAP_FILE,
                "api_url": API_BASE_URL,
                "queries_count": len(TEST_QUERIES),
                "results": self.results
            }, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")
        
    def print_summary(self):
        """Print test summary"""
        print(f"\n\n{'='*80}")
        print("📊 TEST SUMMARY")
        print(f"{'='*80}")
        
        successful = len([r for r in self.results if 'response' in r])
        failed = len([r for r in self.results if 'error' in r])
        
        print(f"✅ Successful queries: {successful}/{len(TEST_QUERIES)}")
        print(f"❌ Failed queries: {failed}/{len(TEST_QUERIES)}")
        
        if successful > 0:
            durations = [r['duration'] for r in self.results if 'duration' in r]
            avg_duration = sum(durations) / len(durations)
            print(f"⏱️  Average response time: {avg_duration:.2f}s")
            print(f"⏱️  Min response time: {min(durations):.2f}s")
            print(f"⏱️  Max response time: {max(durations):.2f}s")
            
async def main():
    """Main test function"""
    print("🚀 5G Callflow Analyzer Test Suite")
    print(f"📁 Testing with: {PCAP_FILE}")
    print(f"🔗 API endpoint: {API_BASE_URL}")
    
    # Check if backend is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE_URL}/") as resp:
                if resp.status != 200:
                    print("\n❌ Backend is not running! Please start it with:")
                    print("   cd backend && uvicorn main:app --reload")
                    return
    except Exception as e:
        print(f"\n❌ Cannot connect to backend at {API_BASE_URL}")
        print("   Please ensure the backend is running")
        return
        
    tester = CallflowAnalyzerTester()
    
    try:
        await tester.setup()
        
        # Upload PCAP file
        await tester.upload_pcap()
        
        # Run test queries
        await tester.run_test_queries()
        
        # Save results
        tester.save_results()
        
        # Print summary
        tester.print_summary()
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        await tester.cleanup()
        
if __name__ == "__main__":
    asyncio.run(main())