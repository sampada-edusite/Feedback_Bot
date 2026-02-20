from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import models
from llm_service import LLMService
from feedback_processor import FeedbackProcessor
import uuid

# Database Configuration
DATABASE_URL = "sqlite:///./feedback.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Service Singleton
llm_service = LLMService() # uses default 120.0s

@app.on_event("startup")
async def startup_event():
    print("Checking LLM Connection...")
    if await llm_service.check_connection():
        print("LLM Service Online")
    else:
        print("WARNING: LLM Service Untouchable. Check Ollama is running.")

class AnalyzeRequest(BaseModel):
    text: str
    session_id: str | None = None

@app.get("/")
def root():
    return {"status": "Feedback Bot Online", "mode": "State Machine"}

@app.post("/analyze")
async def analyze_feedback(request: AnalyzeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Ensure session_id
    if not request.session_id:
        request.session_id = str(uuid.uuid4())
        
    processor = FeedbackProcessor(llm_service, db)
    
    try:
        result = await processor.process_response(request.text, request.session_id, background_tasks)
        
        return {
            "session_id": request.session_id,
            "message": result["message"], 
            "sentiment": result["sentiment"], 
            "recommendation": result["recommendation"],
            "status": "success"
        }
    except Exception as e:
        print(f"Error processing feedback: {e}")
        return {
            "message": "I'm having trouble connecting right now. Please try again.",
            "status": "error"
        }