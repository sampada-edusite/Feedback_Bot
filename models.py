from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class SurveySession(Base):
    __tablename__ = "survey_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    current_step = Column(String, default="INIT")
    nps_score = Column(Integer, nullable=True)
    customer_segment = Column(String, nullable=True)
    # Store the compressed summary here (ScaleDown data)
    summary_json = Column(JSON, nullable=True)
    
    interactions = relationship("Interaction", back_populates="session")

class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("survey_sessions.session_id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_input = Column(String)
    bot_response = Column(String)
    sentiment_label = Column(String) # Frustrated, Delight, Neutral
    sentiment_score = Column(Float) 
    
    session = relationship("SurveySession", back_populates="interactions")
