import requests
import json
import time

def test_raw_ollama():
    url = "http://127.0.0.1:11434/"
    payload = {
        "model": "llama3.2",
        "prompt": "hi",
        "stream": False
    }
    print(f"Sending request to {url}...")
    start = time.time()
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"Response Status: {response.status_code}")
        print(f"Response Text: {response.text[:200]}...")
        print(f"Time taken: {time.time() - start:.2f}s")
    except Exception as e:
        print(f"Request Failed: {e}")
        print(f"Time taken: {time.time() - start:.2f}s")

if __name__ == "__main__":
    test_raw_ollama()
