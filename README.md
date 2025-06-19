# Smart Scheduler AI Agent

This project is a complete, voice-enabled, and personalized AI agent that helps users find, schedule, modify, and delete meetings. It is built with a Flask backend serving a sophisticated, hybrid web interface where users can interact via typing or voice commands, and even see the agent's step-by-step reasoning.

The core logic is powered by a `SchedulerAgentVoice` class built with LangGraph, enabling complex, multi-turn conversations and intelligent tool use.

## ✨ Key Features

- **Hybrid Web UI:** Type or click the microphone button to talk. Agent replies are spoken and shown as chat.
- **"Show Thoughts" View:** Click "Show thoughts 🤔" to see the agent’s reasoning.
- **Multi-turn Conversation Handling:** Handles incomplete queries and follows up.
- **Smart Conflict Resolution:** Finds next free slot if a requested time is busy.
- **Full Calendar Control:** Create, check availability, reschedule, and delete meetings.
- **Persistent State:** Tracks conversation using session IDs.

## 🚀 Tech Stack

- **Backend:** Python + Flask
- **Orchestration:** LangGraph (via LangChain)
- **LLM Provider:** Google Gemini / Cohere (switchable)
- **Frontend:** HTML + CSS + JS (with voice input support)
- **Calendar Integration:** Google Calendar API

## 🔧 Tools (Names)

- `get_todays_date`
- `set_user_home_timezone`
- `retrieve_user_timezone`
- `check_availability`
- `create_meeting`
- `delete_calendar_event`
- `reschedule_calendar_event`

## 🛠️ Setup and Run Instructions

### 1. Clone & Install

```bash
git clone https://github.com/Debajyoti2004/SmartSchedulerAgent.git
cd SmartSchedulerAgent
python -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
pip install -r requirements.txt
```
