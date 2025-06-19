import os
import uuid
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from dotenv import load_dotenv


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scheduler_voice_agent import SchedulerAgentVoice

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

scheduler_agent = SchedulerAgentVoice(user_id="webapp_user_01", user_name="Debajyoti", use_tts=False)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=['POST'])
def chat_handler():
    data = request.get_json()
    user_input = data.get("user_input")
    session_id = data.get("session_id")

    if not session_id:
        session_id = f"web_session_{uuid.uuid4()}"

    response_data = scheduler_agent.get_agent_response(session_id, user_input)
    response_data["session_id"] = session_id
    
    return jsonify(response_data)

if __name__ == "__main__":
    app.run(port=8000, debug=False)