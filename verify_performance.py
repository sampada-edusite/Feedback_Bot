
import asyncio
import httpx
import time
import json

BASE_URL = "http://127.0.0.1:8000"

async def test_performance():
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Warmup / Check Health
        try:
            resp = await client.get(BASE_URL + "/")
            print(f"Health Check: {resp.status_code}")
        except Exception as e:
            print(f"Health Check Failed: {e}")
            return

        session_id = f"test-{int(time.time())}"
        
        # 2. Test NPS (Instant)
        print("\n--- Testing NPS (Regex Optimization) ---")
        start = time.time()
        payload = {"text": "10", "session_id": session_id}
        resp = await client.post(BASE_URL + "/analyze", json=payload)
        duration = time.time() - start
        print(f"NPS Response Time: {duration:.4f}s")
        print(f"Response: {resp.json().get('message')}")
        if duration < 1.0:
            print("[PASS] NPS Optimization: PASS (Instant)")
        else:
            print("[FAIL] NPS Optimization: FAIL (Too Slow)")

        # 3. Test Text Feedback (LLM but Async Recovery)
        print("\n--- Testing Text Feedback (LLM) ---")
        start = time.time()
        payload = {"text": "I really enjoyed the speed of the service, but the colors are a bit bright.", "session_id": session_id}
        resp = await client.post(BASE_URL + "/analyze", json=payload)
        duration = time.time() - start
        print(f"Text Response Time: {duration:.4f}s")
        print(f"Response: {resp.json().get('message')}")
        
        # We expect this to be < 30s (timeout) and faster than before bc no recovery await
        if duration < 15.0:
             print("[PASS] LLM Optimization: PASS (Fast)")
        elif duration < 35.0:
             print("[WARN] LLM Optimization: OK (Acceptable)")
        else:
             print("[FAIL] LLM Optimization: FAIL (Slow)")

if __name__ == "__main__":
    asyncio.run(test_performance())
