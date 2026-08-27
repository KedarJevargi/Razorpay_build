import sys
import os
import asyncio
import httpx
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



async def run_api_test():
    print("\n--- Testing Phase 6: APIs & Observability ---")
    
    # Run the server manually via `uvicorn backend.api.main:app --port 8000 &` before testing
    # For automated tests, we assume it's running locally on port 8000
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Test 1: Fetch AgentCard
            print("\n[1] Fetching AgentCard from /.well-known/agent.json")
            resp = await client.get(f"{base_url}/.well-known/agent.json")
            resp.raise_for_status()
            print("✅ AgentCard retrieved:")
            print(resp.json())
            
            # Test 2: Send Task to Orchestrator via POST /api/jsonrpc
            print("\n[2] Sending A2A Task to /api/jsonrpc")
            intent_msg = "Context: Merchant=merch_adventurehub, Session=test_session_phase6. What tents do you have in stock?"
            
            jsonrpc_payload = {
                "jsonrpc": "2.0",
                "method": "SendMessage",
                "params": {
                    "message": {
                        "role": "ROLE_USER",
                        "parts": [{"text": intent_msg}]
                    },
                    "metadata": {
                        "session_id": "test_session_phase6"
                    }
                },
                "id": "1"
            }
            
            resp = await client.post(
                f"{base_url}/api/jsonrpc",
                json=jsonrpc_payload,
                headers={"A2A-Version": "1.0"}
            )
            resp.raise_for_status()
            print("✅ Task processed successfully:")
            print(resp.json())
            
            # Test 3: Fetch Audit Trail
            print("\n[3] Fetching Audit Trail from /api/audit")
            resp = await client.get(f"{base_url}/api/audit?limit=5")
            resp.raise_for_status()
            audit_logs = resp.json()
            print(f"✅ Retrieved {len(audit_logs)} audit logs.")
            for log in audit_logs:
                print(f"  - [{log['timestamp']}] {log['agent']}: {log['action']}")
                
            # Test 4: Fetch Revenue Metrics
            print("\n[4] Fetching Revenue Metrics from /api/revenue")
            resp = await client.get(f"{base_url}/api/revenue")
            resp.raise_for_status()
            print("✅ Revenue Metrics:")
            print(resp.json())
            
        except httpx.ConnectError:
            print(f"❌ Connection error. Is the FastAPI server running on {base_url}?")
            print("Run `uvicorn backend.api.main:app --port 8000` in another terminal.")
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_api_test())
