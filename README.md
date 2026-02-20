# Feedback Bot 🤖

A high-performance, AI-powered feedback collection bot that uses a state machine for structured conversation and a local LLM (Ollama) for sentiment analysis and recovery actions.

## 🚀 Features

-   **Smart Conversation Flow**: Uses a deterministic State Machine for reliable survey progression (NPS -> Deep Dive -> CSAT).
-   **Real-time Analysis**: Analyzing text feedback using local LLMs (Llama 3.2 via Ollama) to detect sentiment (Frustrated/Delight/Neutral).
-   **Instant NPS**: fast-path regex processing for numerical scores (0.05s response time).
-   **Async Architecture**: Non-blocking logging and background task processing for optimal performance.
-   **Resilient**: built-in retry logic and circuit breakers for LLM connectivity.
-   **Beautiful UI**: Glassmorphism design with a vibrant, modern interface.

## 📦 Prerequisites

1.  **Python 3.10+**
2.  **Ollama**: Must be installed and running.
    -   Pull the model: `ollama pull llama3.2`

## 🛠️ Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 🏃‍♂️ Usage

### 1. Start the Backend Server

Run the FastAPI server with Uvicorn:

```bash
uvicorn main:app --reload
```
*The server will start at `http://127.0.0.1:8000`.*

### 2. Open the Frontend

Simply open `index.html` in your web browser. You can drag and drop the file or use a simple HTTP server.

## 🧪 Testing & Verification

We include several scripts to verify performance and logic:

-   `debug_llm.py`: Tests raw LLM connection and sentiment analysis.
-   `verify_performance.py`: Measures response latency (NPS vs. LLM).
-   `verify_loop.py`: Verifies the conversation reset logic.

## 📁 Project Structure

-   `main.py`: FastAPI entry point and background task handling.
-   `feedback_processor.py`: Core logic for State Machine and feedback handling.
-   `llm_service.py`: Interface for Ollama interactions with retry logic.
-   `models.py`: SQLAlchemy database models.
-   `index.html`: The client-side chat interface.

## ⚡ Performance Optimization

-   **NPS**: Processed via Regex (Instant).
-   **Timeout**: LLM Timeout set to **30s**.
-   **Concurrency**: Logging to `feedback_log.txt` is asynchronous.
