# Smart Scheduler AI Agent

This project is a complete, voice-enabled, and personalized AI agent that helps users find, schedule, modify, and delete meetings. It is built with a Flask backend serving a sophisticated, hybrid web interface where users can interact via typing or voice commands, and even see the agent's step-by-step reasoning.

The core logic is powered by a `SchedulerAgentVoice` class built with LangGraph, enabling complex, multi-turn conversations and intelligent tool use.

## ✨ Key Features

- **Hybrid Web UI:** Type or click the microphone button to talk.
- **🗣️ Realistic AI Voice:** Powered by **ElevenLabs** for natural-sounding spoken responses.
- **🎙️ Offline Speech Recognition:** Uses **Vosk** for private, fast, and reliable voice input.
- **"Show Thoughts" View:** Click "Show thoughts 🤔" to see the agent’s step-by-step reasoning.
- **Multi-turn Conversation Handling:** Handles incomplete queries and follows up.
- **Smart Conflict Resolution:** Finds the next free slot if a requested time is busy.
- **Full Calendar Control:** Create, check availability, reschedule, and delete meetings.
- **Persistent State:** Tracks conversation using session IDs.

## 🚀 Tech Stack

- **Backend:** Python + Flask
- **Orchestration:** LangGraph (via LangChain)
- **LLM Provider:** Google Gemini / Cohere (switchable)
- **Speech-to-Text (STT):** **Vosk (Offline Model)**
- **Text-to-Speech (TTS):** **ElevenLabs**
- **Frontend:** HTML + CSS + JS (with voice input support)
- **Calendar Integration:** Google Calendar API, DateParser

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

Here is the exact section you can **copy-paste into your `README.md`** after the setup block:

---

### 2. Setup Google Calendar Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project and enable the **Google Calendar API**.
3. Configure the OAuth consent screen (set to **External** and add your email as a test user).
4. Create **OAuth client credentials** → Choose **Desktop App**.
5. Download the credentials file and save it to:

```
SmartSchedulerAgent/auth/credentials.json
```

The file must be named exactly: `credentials.json`

---

### 3. Configure `.env`

Create a `.env` file in the root of the project with the following content (adjust paths if needed):

```
TOKEN_PATH=C:/Users/YourName/.../SmartSchedulerAgent/auth/token.json
CREDENTIALS_PATH=C:/Users/YourName/.../SmartSchedulerAgent/auth/credentials.json
GOOGLE_CALENDAR_ID=your-email@gmail.com
GOOGLE_API_KEY=your-google-api-key
COHERE_API_KEY=your-cohere-api-key
ELEVENLABS_API_KEY="your-api-key"
VSOK_MODEL_PATH=C:/Users/YourName/.../SmartSchedulerAgent/model
USERS_TIMEZONES_PATH=C:/Users/YourName/.../SmartSchedulerAgent/auth/users_timezones.pkl
SESSION_MEMORY_PATH=C:/Users/YourName/.../SmartSchedulerAgent/auth/session_memory.pkl
VECTOR_STORE_PATH=C:/Users/YourName/.../SmartSchedulerAgent/auth/faiss_index
```

Replace paths with your actual machine path. Avoid using backslashes (`\`) in `.env`—use forward slashes (`/`).

---

### 4. Run the App

```bash
cd App
python app.py
```

Then open your browser to:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

The first time the calendar tool is used, follow the printed URL in the terminal to authenticate and create `token.json`.

### 5.Agent Flow Diagram

![image](https://github.com/user-attachments/assets/9723a776-5ad3-4156-b46b-6b3f492557cb)

![Screenshot 2025-06-19 192041](https://github.com/user-attachments/assets/348c47c6-0e41-4bbb-b8f0-6faa87bdabd1)

![image](https://github.com/user-attachments/assets/57770126-e953-44f4-ab2b-5867917e2459)

### 6.Demo Video of Enable And Disabling Voice mode

https://github.com/user-attachments/assets/cddf62d5-7499-4e2f-b07b-924f7964e6a6
