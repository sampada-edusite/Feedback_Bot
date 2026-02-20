from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field
import json
import asyncio

class SentimentAnalysis(BaseModel):
    score: float = Field(description="Sentiment score between -1.0 and 1.0")
    label: str = Field(description="Sentiment label: Frustrated, Delight, or Neutral")
    keywords: list[str] = Field(description="List of key topics or words")

class ScaleDownSummary(BaseModel):
    topics: list[str] = Field(description="List of discussed topics")
    key_pain_point: str = Field(description="Main issue or pain point identified")
    metrics: dict = Field(description="Inferred metrics like NPS or CSAT from text")

import httpx

class LLMService:
    def __init__(self, model_name="llama3.2", timeout=30.0):
        # low temperature for deterministic JSON output
        self.model_name = model_name
        self.timeout = timeout
        # hardcode base_url to avoid localhost issues
        base_url = "http://127.0.0.1:11434"
        # keep_alive="5m" keeps the model loaded for 5 minutes after request
        self.llm_json = ChatOllama(model=model_name, format="json", temperature=0, timeout=timeout, base_url=base_url, num_predict=128, num_ctx=2048, keep_alive="5m")
        self.llm_text = ChatOllama(model=model_name, temperature=0.7, timeout=timeout, base_url=base_url, num_predict=128, num_ctx=2048, keep_alive="5m")
        
    async def _retry_operation(self, operation, retries=1, delay=2):
        """
        Helper to retry async operations with exponential backoff.
        """
        last_exception = None
        for i in range(retries):
            try:
                if i > 0:
                    print(f"Retrying LLM operation ({i}/{retries})...")
                # Enforce timeout with asyncio.wait_for, as underlying lib might hang
                return await asyncio.wait_for(operation(), timeout=self.timeout)
            except asyncio.TimeoutError:
                last_exception = TimeoutError(f"Operation timed out after {self.timeout}s")
                print(f"LLM Timeout (Attempt {i+1})")
            except Exception as e:
                last_exception = e
                print(f"LLM Error (Attempt {i+1}): {e}")
            
            if i < retries - 1:
                await asyncio.sleep(delay * (2 ** i))
                
        raise last_exception

    async def check_connection(self) -> bool:
        """
        Verify connection to Ollama server.
        """
        try:
            # Check if Ollama is running by hitting the root endpoint
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://127.0.0.1:11434/", timeout=5.0)
                return resp.status_code == 200
        except Exception as e:
            print(f"LLM Connection Check Failed: {e}")
            return False

    async def analyze_sentiment(self, text: str) -> dict:
        parser = JsonOutputParser(pydantic_object=SentimentAnalysis)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Analyze the sentiment of the user's feedback. Return JSON with 'score' (-1.0 to 1.0), 'label' (Frustrated, Delight, Neutral), and 'keywords' (list)."),
            ("user", "{text}")
        ])
        chain = prompt | self.llm_json | parser
        
        async def _run():
            return await chain.ainvoke({"text": text})

        try:
            return await self._retry_operation(_run)
        except Exception as e:
            print(f"LLM Sentiment Failed after retries: {e}")
            # Fallback
            return {"score": 0.0, "label": "Neutral", "keywords": []}

    async def generate_recovery_action(self, session_state: dict) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "The user is frustrated. Generate a short, empathetic recovery action or message for a support agent to take. Keep it under 20 words."),
            ("user", "Context: {context}")
        ])
        chain = prompt | self.llm_text | StrOutputParser()
        
        async def _run():
            # Serialize session state safely
            clean_state = {k:v for k,v in session_state.items() if k != 'llm_service'} 
            return await chain.ainvoke({"context": json.dumps(clean_state, default=str)})

        try:
            return await self._retry_operation(_run)
        except Exception as e:
            print(f"LLM Recovery Failed after retries: {e}")
            return "Escalate to human agent immediately."

    async def compress_feedback(self, transcript: str) -> dict:
        parser = JsonOutputParser(pydantic_object=ScaleDownSummary)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Summarize the customer service transcript into a JSON object with 'topics', 'key_pain_point', and 'metrics'."),
            ("user", "{transcript}")
        ])
        chain = prompt | self.llm_json | parser
        
        async def _run():
            return await chain.ainvoke({"transcript": transcript})

        try:
            return await self._retry_operation(_run)
        except Exception as e:
            print(f"LLM Compression Failed after retries: {e}")
            return {"topics": [], "key_pain_point": "Error processing", "metrics": {}}
