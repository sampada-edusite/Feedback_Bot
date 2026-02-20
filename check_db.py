from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import SurveySession, Interaction, Base

DATABASE_URL = "sqlite:///./feedback.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("--- Survey Sessions ---")
sessions = db.query(SurveySession).all()
print(f"Total Sessions: {len(sessions)}")
for s in sessions:
    print(f"ID: {s.session_id} | Step: {s.current_step} | NPS: {s.nps_score}")

print("\n--- Interactions ---")
interactions = db.query(Interaction).all()
print(f"Total Interactions: {len(interactions)}")
for i in interactions:
    print(f"Session: {i.session_id} | User: {i.user_input} | Bot: {i.bot_response}")

db.close()
