import os
import uuid
import threading
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scheduler_voice_agent import SchedulerAgent

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
socketio = SocketIO(app, async_mode='threading')

voice_clients = {}
text_agent = SchedulerAgent(user_id="webapp_user_01", user_name="Debajyoti", use_tts=False)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

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
    thoughts, final_answer = text_agent.get_agent_response(session_id, user_input)
    return jsonify({
        "thoughts": thoughts,
        "final_response": final_answer,
        "session_id": session_id
    })

def run_agent_loop(agent):
    try:
        agent.listen_and_respond()
    except Exception as e:
        print(f"Error running agent loop: {e}")

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    if request.sid in voice_clients:
        agent, thread = voice_clients[request.sid]
        agent.stop_listening()
        thread.join()
        del voice_clients[request.sid]
        print(f"Cleaned up voice agent for SID: {request.sid}")

@socketio.on('start_voice')
def handle_start_voice():
    sid = request.sid
    if sid in voice_clients:
        return
    agent = SchedulerAgent(
        user_id=f"voice_user_{sid}", 
        user_name="Voice User", 
        use_tts=True,
        socketio=socketio, 
        sid=sid
    )
    thread = threading.Thread(target=run_agent_loop, args=(agent,))
    voice_clients[sid] = (agent, thread)
    thread.start()
    socketio.emit('voice_status', {'status': 'started'}, to=sid)

@socketio.on('stop_voice')
def handle_stop_voice():
    sid = request.sid
    if sid in voice_clients:
        agent, thread = voice_clients[sid]
        agent.stop_listening()
        thread.join()
        del voice_clients[sid]
        socketio.emit('voice_status', {'status': 'stopped'}, to=sid)

if __name__ == "__main__":
    socketio.run(app, port=8000, debug=False, allow_unsafe_werkzeug=True)