from llm_service import LLMService
import asyncio

async def test_llm():
    print("Testing LLM Connection with Timeout/Retry...")
    # Use a short timeout for debugging/testing the timeout logic
    service = LLMService(timeout=5.0) 
    
    print("1. Checking Connection (Ping)...")
    if await service.check_connection():
        print("   Connection Successful!")
    else:
        print("   Connection Failed (as expected if Ollama is hanging/down).")

    print("\n2. Testing Sentiment Analysis (Inference)...")
    try:
        response = await service.analyze_sentiment("I love this service!")
        print(f"   Response: {response}")
    except Exception as e:
        print(f"   Inference Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())
