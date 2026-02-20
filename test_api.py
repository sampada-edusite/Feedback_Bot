import urllib.request
import json
import time

url = "http://127.0.0.1:8001/analyze"

def send_feedback(text, session_id=None):
    data = {"text": text}
    if session_id:
        data["session_id"] = session_id
        
    params = json.dumps(data).encode("utf8")
    req = urllib.request.Request(url, data=params, headers={'content-type': 'application/json'})

    start_time = time.time()
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf8'))
        end_time = time.time()
        print(f"  > Latency: {end_time - start_time:.2f}s")
        return result
    except Exception as e:
        print(f"Request Error: {e}")
        return None

# Test Flow
print("--- Starting API Test ---")

# 1. Initial NPS
print("\n1. Sending NPS Score (10)...")
res1 = send_feedback("I give it a 10")
if res1 and res1.get("status") == "success":
    print(f"Success! Session: {res1['session_id']}")
    print(f"Bot: {res1['message']}")
    
    session_id = res1['session_id']
    
    # 2. Follow-up (Favorite Feature)
    print("\n2. Sending Follow-up (The speed)...")
    res2 = send_feedback("The speed of the service.", session_id)
    if res2:
        print(f"Bot: {res2['message']}")
        
        # 3. CSAT
        print("\n3. Sending CSAT (5)...")
        res3 = send_feedback("5 stars", session_id)
        if res3:
             print(f"Bot: {res3['message']}")
             
else:
    print("Failed to start session.")
    print(res1)
