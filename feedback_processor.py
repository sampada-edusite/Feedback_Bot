import datetime
import re
from sqlalchemy.orm import Session
from models import SurveySession, Interaction
from llm_service import LLMService

class FeedbackProcessor:
    def __init__(self, llm_service: LLMService, db_session: Session):
        self.llm = llm_service
        self.db = db_session

    def get_or_create_session(self, session_id: str) -> SurveySession:
        session = self.db.query(SurveySession).filter(SurveySession.session_id == session_id).first()
        if not session:
            # New session, start at NPS_ASK
            session = SurveySession(session_id=session_id, current_step="NPS_ASK")
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
        return session

    async def process_response(self, user_input: str, session_id: str, background_tasks=None):
        # 1. Get Session
        session = self.get_or_create_session(session_id)
        
        # FIX: Check if session is already closed, if so, restart it
        if session.current_step == "CLOSING":
            session.current_step = "NPS_ASK"
            session.nps_score = None
            session.end_time = None
            # Ideally archive old interactions, but for now we append to same session or just restart flow
            self.db.commit()
        
        # 2. Analyze Sentiment (Optimized)
        sentiment_result = None
        if session.current_step == "NPS_ASK":
            score = self.extract_score(user_input)
            if score is not None:
                # Fast path for NPS
                sentiment_result = {
                    'score': (score / 5.0) - 1.0, # Map 0-10 to -1..1 roughly, or just dummy
                    'label': 'Neutral', 
                    'keywords': []
                }
        
        if not sentiment_result:
            sentiment_result = await self.llm.analyze_sentiment(user_input)
        
        # 3. Log Interaction
        interaction = Interaction(
            session_id=session_id,
            user_input=user_input,
            sentiment_label=sentiment_result.get('label', 'Neutral'),
            sentiment_score=sentiment_result.get('score', 0.0)
        )
        self.db.add(interaction)
        
        # 4. Determine Next Response & State
        next_step, bot_response = await self.run_state_machine(session, user_input, sentiment_result)
        
        # 5. Update Session State
        session.current_step = next_step
        interaction.bot_response = bot_response
        self.db.commit()
        
        # 6. Background Tasks (Logging & Recovery)
        if background_tasks:
            # Prepare data for logging since we can't pass DB objects easily if session closes
            log_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "session_id": session_id,
                "user_input": user_input,
                "sentiment": sentiment_result.get('label'),
                "score": sentiment_result.get('score'),
                "bot_response": bot_response
            }
            background_tasks.add_task(self.log_to_file, log_data)

            # Check for recovery (conceptually) - we won't block for it
            # If we really needed it, we'd add_task here. 
            # Since frontend doesn't use it, we skip the blocking call entirely.
        
        return {
            "message": bot_response,
            "sentiment": sentiment_result.get('label'),
            "recommendation": None, # Removed blocking call
            "status": "success"
        }

    def log_to_file(self, data: dict):
        try:
            with open("feedback_log.txt", "a", encoding="utf-8") as f:
                f.write(str(data) + "\n")
        except Exception as e:
            print(f"Failed to write log: {e}")

    async def run_state_machine(self, session, user_input, sentiment):
        """
        Returns (next_state, bot_message) based on current_state + input
        """
        import random
        curr = session.current_step
        
        # Responses
        responses = {
            "DEEP_DIVE": [
                "I'm sorry to hear that. Could you tell us what specifically went wrong?",
                "That's disappointing. What was the main issue you faced?",
                "We aim to do better. Can you share more details about what happened?"
            ],
            "REASONING": [
                "Thank you. What is one thing we could do to improve?",
                "Got it. Any specific suggestions for us?",
                "Thanks for the score. How can we make your experience 10/10?"
            ],
            "FAVORITE_FEATURE": [
                "That's wonderful! What did you enjoy the most?",
                "Glad to hear it! What was the highlight for you?",
                "Fantastic! What feature did you like best?"
            ],
            "CSAT_ASK_FRUSTRATED": [
                "I understand your frustration and have flagged this for our team. To wrap up, how would you rate this chat experience (1-5)?",
                "I'm sorry for the trouble. I've noted your issues. How would you rate this support chat (1-5)?",
                "Your feedback is important. Before you go, please rate this chat (1-5)."
            ],
            "CSAT_ASK_NORMAL": [
                "Thanks for sharing! How would you rate this chat experience (1-5)?",
                "Appreciate the feedback! How satisfied were you with this chat (1-5)?",
                "One last question: How would you rate this conversation (1-5)?"
            ],
            "CLOSING": [
                "Thank you for your feedback! Have a great day.",
                "All done! Thanks for your time.",
                "Survey complete. We appreciate your input!"
            ],
            "NPS_RETRY": [
                "I didn't catch that number. On a scale of 0-10, how likely are you to recommend us?",
                "Could you please provide a number between 0 and 10?",
                "Sorry, I need a score from 0 to 10. How likely are you to recommend us?"
            ]
        }
        
        # -- STATE: NPS_ASK (Waiting for score) --
        if curr == "NPS_ASK":
            score = self.extract_score(user_input)
            if score is not None:
                session.nps_score = score
                if score <= 6:
                    return "DEEP_DIVE", random.choice(responses["DEEP_DIVE"])
                elif score <= 8:
                    return "REASONING", random.choice(responses["REASONING"])
                else:
                    return "FAVORITE_FEATURE", random.choice(responses["FAVORITE_FEATURE"])
            else:
                # Invalid input, stay on NPS_ASK
                return "NPS_ASK", random.choice(responses["NPS_RETRY"])

        # -- STATE: DETAIL COLLECTION --
        elif curr in ["DEEP_DIVE", "REASONING", "FAVORITE_FEATURE"]:
            # Transition to CSAT regardless of answer, but use sentiment context
            if sentiment.get('label') == 'Frustrated':
                return "CSAT_ASK", random.choice(responses["CSAT_ASK_FRUSTRATED"])
            
            return "CSAT_ASK", random.choice(responses["CSAT_ASK_NORMAL"])

        # -- STATE: CSAT_ASK --
        elif curr == "CSAT_ASK":
            # Just close
            return "CLOSING", random.choice(responses["CLOSING"])

        # -- STATE: CLOSING --
        elif curr == "CLOSING":
            return "CLOSING", "The survey is complete. Thank you!"

        # Fallback
        return "NPS_ASK", "How likely are you to recommend us (0-10)?"

    def extract_score(self, text):
        # Match single number 0-10, or "10" at start/end/isolated
        # Also handles "I give it a 10" or "rate 5"
        match = re.search(r'\b(10|[0-9])\b', text)
        if match:
            return int(match.group(1))
        return None

    def should_trigger_recovery(self, session):
        # Trigger if last 2 interactions were Frustrated
        # Need to refresh interactions from DB or use the relationship
        # self.db.refresh(session) # might be expensive, rely on lazy load
        interactions = session.interactions
        if len(interactions) < 2:
            return False
        
        # Check last 2
        recent = interactions[-2:] 
        return all(i.sentiment_label == 'Frustrated' for i in recent)

    async def scale_down_survey(self, session):
        # Construct transcript
        transcript = "\n".join([f"User: {i.user_input}\nBot: {i.bot_response}" for i in session.interactions])
        
        summary = await self.llm.compress_feedback(transcript)
        session.summary_json = summary
        self.db.add(session)
        self.db.commit()

