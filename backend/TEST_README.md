# 5G Callflow Analyzer Tests

Test suite for evaluating the o4-mini model's performance on 5G PCAP analysis.

## Quick Start

1. Ensure the backend is running:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Run the quick test:
   ```bash
   ./quick_test.py
   ```

3. Run the comprehensive test suite:
   ```bash
   ./test_analyzer.py
   ```

## Test Scripts

### quick_test.py
- Simple verification that the system works
- Uploads ue0.pcap and runs 2 basic queries
- Good for quick sanity checks

### test_analyzer.py
- Comprehensive test suite with 10 different queries
- Tests various aspects of 5G analysis:
  - Procedure identification
  - Registration flow
  - Error detection
  - Security analysis
  - Performance evaluation
- Saves results to timestamped JSON file
- Provides performance metrics

## Test Queries

The test suite evaluates o4-mini on these 5G analysis tasks:

1. Main procedures identification
2. UE registration procedure analysis
3. Error and failure detection
4. NGAP message analysis
5. NAS security setup
6. PDU session establishment
7. Authentication procedures
8. Key identifier extraction
9. Call flow summarization
10. Performance analysis

## Output

- Console output with real-time results
- JSON file with complete test results
- Performance metrics (response times)
- Success/failure summary

## Interpreting Results

Good o4-mini responses should:
- Accurately identify 5G procedures
- Provide technical details about protocols
- Maintain context across queries
- Give structured, clear explanations
- Identify specific message types and flows