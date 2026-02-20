
import asyncio
import httpx
import time

BASE_URL = "http://127.0.0.1:8000"

async def test_loop_fix():
    async with httpx.AsyncClient(timeout=60.0) as client:
        session_id = f"test-loop-{int(time.time())}"
        
        print(f"--- Starting Session {session_id} ---")
        
        # 1. Provide NPS
        await client.post(BASE_URL + "/analyze", json={"text": "10", "session_id": session_id})
        
        # 2. Provide Feedback (Reach Closing)
        resp = await client.post(BASE_URL + "/analyze", json={"text": "Great!", "session_id": session_id})
        # Depending on logic, might need 1 or 2 steps to close. 
        # NPS > 8 -> FAVORITE_FEATURE -> CSAT -> CLOSING
        
        print(f"Response 2: {resp.json()['message']}")
        
        # 3. Force Close (if not already)
        resp = await client.post(BASE_URL + "/analyze", json={"text": "5", "session_id": session_id}) # CSAT
        print(f"Response 3 (Should be Closing): {resp.json()['message']}")
        
        # 4. SEND NEW MESSAGE (The Bug Trigger)
        print("\n--- Triggering Bug (Sending message after closed) ---")
        resp = await client.post(BASE_URL + "/analyze", json={"text": "Hello?", "session_id": session_id})
        msg = resp.json()['message']
        print(f"Response 4: {msg}")
        
        if "likely to recommend" in msg.lower() or "0-10" in msg:
            print("[PASS] Loop Fix: Session Restarted ✅")
        elif "survey is complete" in msg.lower():
            print("[FAIL] Loop Fix: Still Stuck in Loop ❌")
        else:
            print(f"[?] Unknown State: {msg}")

if __name__ == "__main__":
    asyncio.run(test_loop_fix())
