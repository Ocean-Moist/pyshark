from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyshark
import os
import tempfile
import asyncio
from typing import List, Dict, Any, Optional
import json
import openai
from datetime import datetime
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Model configuration
MODEL = "o4-mini"  # Latest OpenAI reasoning model

app = FastAPI(title="5G Callflow Analyzer")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State management for Jupyter-style kernel
class AnalysisKernel:
    def __init__(self):
        self.state = {}
        self.imports = set()
        self.files = {}
        self.history = []
        
    def add_file(self, file_id: str, file_path: str):
        self.files[file_id] = file_path
        
    def get_file(self, file_id: str) -> Optional[str]:
        return self.files.get(file_id)
        
    def add_to_history(self, entry: Dict[str, Any]):
        self.history.append(entry)
        
    def get_state(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "imports": list(self.imports),
            "files": self.files,
            "history": self.history
        }

# Global kernel instance
kernel = AnalysisKernel()

class ChatMessage(BaseModel):
    role: str
    content: str
    file_id: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    file_id: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "5G Callflow Analyzer API"}

@app.post("/upload")
async def upload_pcap(file: UploadFile = File(...)):
    """Upload a PCAP file for analysis"""
    if not file.filename.endswith('.pcap'):
        raise HTTPException(status_code=400, detail="Only PCAP files are allowed")
    
    # Generate unique file ID
    content = await file.read()
    file_id = hashlib.md5(content).hexdigest()[:8]
    
    # Save file temporarily
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Store in kernel
    kernel.add_file(file_id, file_path)
    
    # Basic PCAP info - run pyshark in a thread to avoid event loop conflicts
    try:
        import threading
        import queue
        
        result_queue = queue.Queue()
        
        def count_packets():
            try:
                cap = pyshark.FileCapture(file_path, keep_packets=False)
                count = 0
                for packet in cap:
                    count += 1
                    if count >= 10000:  # Safety limit
                        break
                cap.close()
                result_queue.put(("success", count))
            except Exception as e:
                result_queue.put(("error", e))
        
        # Run in a separate thread
        thread = threading.Thread(target=count_packets)
        thread.start()
        thread.join(timeout=30)  # 30 second timeout
        
        if thread.is_alive():
            raise Exception("Packet counting timed out")
            
        result_type, result_value = result_queue.get()
        if result_type == "error":
            raise result_value
            
        packet_count = result_value
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content),
            "packet_count": packet_count,
            "message": f"Successfully uploaded {file.filename}"
        }
    except Exception as e:
        import traceback
        error_detail = f"Error processing PCAP: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(status_code=500, detail=f"Error processing PCAP: {type(e).__name__}: {str(e)}")

@app.post("/analyze")
async def analyze_pcap(request: ChatRequest):
    """Analyze PCAP file using AI"""
    try:
        # Get file path if provided
        file_path = None
        if request.file_id:
            file_path = kernel.get_file(request.file_id)
            if not file_path:
                raise HTTPException(status_code=404, detail="File not found")
        
        # Extract comprehensive PCAP data if file is provided
        context = ""
        if file_path:
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def extract_all_data():
                try:
                    # Get all 5G-related packets with full field extraction
                    cap = pyshark.FileCapture(
                        file_path,
                        display_filter="ngap || nas-5gs || nas-eps || sctp || pfcp || gtp",
                        decode_as={'sctp.port==38412': 'ngap', 'udp.port==8805': 'pfcp'}
                    )
                    
                    all_packets = []
                    ngap_packets = []
                    nas_packets = []
                    pdu_session_packets = []
                    
                    for i, packet in enumerate(cap):
                        if i >= 50:  # Reduce initial packet analysis
                            break
                            
                        packet_data = {
                            "number": str(packet.number),
                            "time": str(packet.sniff_time),
                            "length": str(packet.length),
                            "protocols": [str(l.layer_name) for l in packet.layers],
                            "summary": str(packet) if hasattr(packet, '__str__') else "",
                            "fields": {}
                        }
                        
                        # Extract ALL fields from ALL layers
                        for layer in packet.layers:
                            layer_name = str(layer.layer_name)
                            packet_data["fields"][layer_name] = {}
                            
                            # Get all field names and values
                            for field_name in layer.field_names:
                                try:
                                    field_value = getattr(layer, field_name, None)
                                    if field_value is not None:
                                        packet_data["fields"][layer_name][field_name] = str(field_value)
                                except:
                                    pass
                            
                            # Special handling for specific protocols
                            if layer_name == "ngap":
                                ngap_packets.append(packet_data)
                                # Try to get PDU session info
                                if any(key for key in packet_data["fields"].get("ngap", {}).keys() 
                                       if "pdu" in key.lower() or "qos" in key.lower()):
                                    pdu_session_packets.append(packet_data)
                            
                            elif layer_name in ["nas-5gs", "nas_5gs", "nas-eps"]:
                                nas_packets.append(packet_data)
                        
                        all_packets.append(packet_data)
                    
                    cap.close()
                    
                    # Organize results
                    results = {
                        "total_packets": len(all_packets),
                        "ngap_packets": len(ngap_packets),
                        "nas_packets": len(nas_packets),
                        "pdu_session_related": len(pdu_session_packets),
                        "all_packets": all_packets,
                        "ngap_samples": ngap_packets[:10],
                        "nas_samples": nas_packets[:10],
                        "pdu_session_samples": pdu_session_packets[:10]
                    }
                    
                    result_queue.put(results)
                except Exception as e:
                    result_queue.put({"error": str(e)})
            
            # Run extraction in thread
            thread = threading.Thread(target=extract_all_data)
            thread.start()
            thread.join(timeout=60)
            
            if thread.is_alive():
                raise Exception("Packet extraction timed out")
                
            pcap_data = result_queue.get()
            
            if isinstance(pcap_data, dict) and "error" in pcap_data:
                raise Exception(pcap_data["error"])
            
            # Create minimal context for tool-based approach
            context = f"\n\nPCAP file loaded: {os.path.basename(file_path)}\n"
            context += f"Initial scan found:\n"
            context += f"- Total packets: {pcap_data['total_packets']} (first 50 analyzed)\n"
            context += f"- NGAP packets: {pcap_data['ngap_packets']}\n"  
            context += f"- NAS packets: {pcap_data['nas_packets']}\n"
            context += f"- PDU Session related: {pcap_data['pdu_session_related']}\n\n"
            context += "Use the analyze_pcap tool to search for specific information like QoS parameters.\n"
        
        # Prepare messages for OpenAI - o4-mini specific prompt for tool usage
        system_prompt = """You are a 5G control plane traffic analyzer with access to a PCAP analysis tool.

        You have the analyze_pcap tool that lets you search packets by:
        - display_filter: Wireshark filters like "ngap", "nas-5gs", "pfcp", or complex filters
        - field_patterns: Search for fields containing specific patterns like "qos", "qfi", "bitrate", "gbr", "mbr"
        
        For QoS analysis:
        1. First search PDU Session packets: display_filter="ngap" with field_patterns=["qos", "qfi", "5qi", "bitrate", "gbr", "mbr"] 
        2. Also check PFCP packets: display_filter="pfcp" with field_patterns=["qos", "pdr", "far", "qer"]
        3. Look for fields like:
           - qosFlowLevelQosParameters
           - qfi (QoS Flow Identifier)  
           - fiveQI or 5qi
           - gbrQosInformation
           - maximumBitRate, guaranteedFlowBitRate
           - priorityLevelQos
        
        Always use the tool to get actual data before answering."""
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add chat history with context
        for i, msg in enumerate(request.messages):
            if i == 0 and context:  # Add context to first user message
                messages.append({"role": msg.role, "content": msg.content + context})
            else:
                messages.append({"role": msg.role, "content": msg.content})
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Define tool for pyshark analysis (tools replaced functions in newer API)
        analyze_pcap_tool = {
            "type": "function",
            "function": {
                "name": "analyze_pcap",
                "description": "Analyze PCAP file using pyshark with filters to extract specific packet data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "display_filter": {
                            "type": "string",
                            "description": "Wireshark display filter (e.g., 'ngap', 'nas-5gs', 'sctp.port==38412')"
                        },
                        "field_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Pattern to search for in field names (e.g., 'qos', 'qfi', 'bitrate')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of packets to analyze (default: 200)"
                        }
                    },
                    "required": ["display_filter"]
                }
            }
        }
        
        # Function to execute pyshark analysis
        def execute_analyze_pcap(display_filter, field_patterns=None, limit=200):
            if not file_path:
                return {"error": "No PCAP file loaded"}
                
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def run_analysis():
                try:
                    cap = pyshark.FileCapture(
                        file_path,
                        display_filter=display_filter,
                        decode_as={'sctp.port==38412': 'ngap', 'udp.port==8805': 'pfcp'}
                    )
                    
                    results = []
                    for i, packet in enumerate(cap):
                        if i >= limit:
                            break
                            
                        packet_data = {
                            "number": str(packet.number),
                            "time": str(packet.sniff_time),
                            "summary": str(packet) if hasattr(packet, '__str__') else "",
                            "matching_fields": {}
                        }
                        
                        # Extract fields matching patterns
                        for layer in packet.layers:
                            layer_name = str(layer.layer_name)
                            for field_name in layer.field_names:
                                # Check if field matches any pattern
                                if field_patterns:
                                    for pattern in field_patterns:
                                        if pattern.lower() in field_name.lower():
                                            try:
                                                value = getattr(layer, field_name, None)
                                                if value is not None:
                                                    if layer_name not in packet_data["matching_fields"]:
                                                        packet_data["matching_fields"][layer_name] = {}
                                                    packet_data["matching_fields"][layer_name][field_name] = str(value)
                                            except:
                                                pass
                                else:
                                    # No patterns, get all fields
                                    try:
                                        value = getattr(layer, field_name, None)
                                        if value is not None:
                                            if layer_name not in packet_data["matching_fields"]:
                                                packet_data["matching_fields"][layer_name] = {}
                                            packet_data["matching_fields"][layer_name][field_name] = str(value)
                                    except:
                                        pass
                        
                        if packet_data["matching_fields"]:  # Only include packets with matching fields
                            results.append(packet_data)
                    
                    cap.close()
                    result_queue.put({
                        "packets_found": len(results),
                        "filter_used": display_filter,
                        "patterns_searched": field_patterns,
                        "results": results
                    })
                except Exception as e:
                    result_queue.put({"error": str(e)})
            
            thread = threading.Thread(target=run_analysis)
            thread.start()
            thread.join(timeout=30)
            
            if thread.is_alive():
                return {"error": "Analysis timed out"}
                
            return result_queue.get()
        
        # Try with tools parameter for o4-mini
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=[analyze_pcap_tool],
                tool_choice="auto",
                max_completion_tokens=5000,
                reasoning_effort="high"
            )
            
            response_message = response.choices[0].message
            
            # Handle tool calls
            if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                # Execute all tool calls
                tool_results = []
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "analyze_pcap":
                        function_args = json.loads(tool_call.function.arguments)
                        result = execute_analyze_pcap(**function_args)
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                
                # Add tool call and results to messages
                messages.append(response_message)
                for result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "content": result["output"]
                    })
                
                # Get final response
                final_response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_completion_tokens=5000,
                    reasoning_effort="high"
                )
                
                response_content = final_response.choices[0].message.content
            else:
                response_content = response_message.content
                
        except Exception as e:
            # If tools not supported, fall back to providing all data upfront
            if "tools" in str(e) or "tool" in str(e):
                print(f"Tools not supported, using data extraction approach: {e}")
                # Just use the response from the context-enriched prompt
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_completion_tokens=5000,
                    reasoning_effort="high"
                )
                response_content = response.choices[0].message.content
            else:
                raise e
        
        # Store in history
        kernel.add_to_history({
            "timestamp": datetime.now().isoformat(),
            "request": request.dict(),
            "response": response_content
        })
        
        return {
            "response": response_content,
            "model_used": MODEL,
            "kernel_state": kernel.get_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/state")
async def get_kernel_state():
    """Get current kernel state"""
    return kernel.get_state()

@app.post("/reset")
async def reset_kernel():
    """Reset the kernel state"""
    global kernel
    kernel = AnalysisKernel()
    return {"message": "Kernel reset successfully"}
