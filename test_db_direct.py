
from sqlalchemy import create_engine, text
import time

# Wait for server to potentially start if we were running it, 
# but here we assume the user might run it or we just check the db creation after a request.
# For this agentic context, I'll rely on the existing main.py structure. 
# Since I can't easily start the uvicorn server in background and hit it in the same session reliably without blocking, 
# I will instead mock the DB interaction or just rely on importing the app/db logic if possible, 
# OR just instruct the user to run it. 
# However, the user asked me to refactor. I should verify if possible.

# Actually, I can import the functions from main to test the DB logic directly without running the full server.
from main import SessionLocal, Feedback

# Create a session
db = SessionLocal()

# Create a new feedback entry directly to test DB connection
print("Testing Database Connection and Insertion...")
try:
    fb = Feedback(feedback_text="This is a test feedback", sentiment="Positive")
    db.add(fb)
    db.commit()
    print(f"Successfully added feedback with ID: {fb.id}")
    
    # Query it back
    fetched = db.query(Feedback).filter(Feedback.id == fb.id).first()
    print(f"Retrieved Feedback: {fetched.feedback_text} | Sentiment: {fetched.sentiment}")
    assert fetched.feedback_text == "This is a test feedback"
    
    # Clean up
    db.delete(fetched)
    db.commit()
    print("Test passed and cleaned up.")
except Exception as e:
    print(f"Test Failed: {e}")
finally:
    db.close()
