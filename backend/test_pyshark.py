#!/usr/bin/env python3
import pyshark
import os

pcap_file = "../ue0.pcap"
print(f"Testing pyshark with {pcap_file}")
print(f"File exists: {os.path.exists(pcap_file)}")
print(f"Absolute path: {os.path.abspath(pcap_file)}")

try:
    cap = pyshark.FileCapture(pcap_file)
    packets = []
    for i, packet in enumerate(cap):
        if i >= 5:  # Just get first 5 packets
            break
        packets.append(packet)
        print(f"Packet {i+1}: {packet}")
    cap.close()
    print(f"\nSuccessfully read {len(packets)} packets")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()