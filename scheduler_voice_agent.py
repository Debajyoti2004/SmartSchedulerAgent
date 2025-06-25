import pygame
import threading
import time
import os
import pyaudio
import io
import json
import vosk
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from SchedulerAgent import (
    add_conversation_to_memory,
    compile_agent_workflow
)

load_dotenv()

class SchedulerAgent:
    def __init__(self, user_id: str, user_name: str, use_tts: bool = True, socketio=None, sid=None):
        print("▶️  Initializing SchedulerAgent...")
        self.user_id = user_id
        self.user_name = user_name
        self.use_tts = use_tts
        self.socketio = socketio
        self.sid = sid
        self.scheduler_agent = compile_agent_workflow()
        self.current_session_id = f"voice_session_{user_id}"
        self.stop_listening_event = threading.Event()
        self.speak_thread = None

        try:
            pygame.mixer.init()
            print("🔊 Pygame mixer initialized.")
        except Exception as e:
            print(f"❌ Could not initialize pygame mixer: {e}. Audio playback will be disabled.")
            self.use_tts = False

        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.elevenlabs_api_key:
            raise ValueError("❌ ELEVENLABS_API_KEY not found in environment variables.")
        self.eleven_client = ElevenLabs(api_key=self.elevenlabs_api_key)
        self.voice_id = 'Rm2gUL5RDvWycN1zoSM4'
        
        print("➡️  Loading offline speech recognition model...")
        model_path = os.getenv("VSOK_MODEL_PATH")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ Vosk model not found at path: {model_path}.")
        
        try:
            self.vosk_model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(self.vosk_model, 16000)
            self.recognizer.SetWords(False)
            print("✔️  Offline model loaded successfully.")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to load Vosk model: {e}")

        self.pyaudio_instance = None
        self.pyaudio_stream = None
        print("✅ Agent initialized successfully.")

    def _handle_final_transcript(self, transcript: str):
        print(f"👤 YOU: {transcript}")
        if self.socketio:
            self.socketio.emit('user_transcript', {'transcript': transcript}, to=self.sid)
        self.stop_speaking()
        print("🧠 Thinking...")
        thoughts, final_response = self.get_agent_response(self.current_session_id, transcript)
        for idx, thought in enumerate(thoughts, 1):
            print(f"🤔 Thought {idx}: {thought.strip()}")
        print(f"🤖 AGENT: {final_response}")
        if self.socketio:
            self.socketio.emit('agent_thoughts', {'thoughts': thoughts}, to=self.sid)
            self.socketio.emit('agent_response', {'response': final_response}, to=self.sid)
        if self.use_tts:
            self.speak(final_response)

    def get_agent_response(self, session_id: str, user_text: str):
        config = RunnableConfig(configurable={"user_id": self.user_id, "thread_id": session_id})
        try:
            response = self.scheduler_agent.invoke(
                input={"messages": [HumanMessage(content=user_text)]},
                config=config, stream_mode="values"
            )
        except Exception as e:
            print(f"❌ Agent invocation failed: {e}")
            return ["Agent failed to respond."], "Sorry, there was an error."
        messages = response.get("messages", [])
        thoughts = [msg.content for msg in messages[:-1]] if len(messages) > 1 else []
        final_response = messages[-1].content if messages else "No response from agent."
        add_conversation_to_memory(
            user_id=self.user_id, session_id=session_id,
            user_input=user_text, agent_response=final_response
        )
        return thoughts, final_response

    def speak(self, text: str):
        print(f"🗣️  Attempting to speak...")
        self.stop_speaking()
        def run_audio_playback():
            if not pygame.mixer.get_init(): return
            try:
                clean_text = text.split("http")[0] if "http" in text else text
                audio_generator = self.eleven_client.text_to_speech.convert(
                    voice_id=self.voice_id, text=clean_text,
                    model_id="eleven_multilingual_v2", output_format="mp3_44100_128"
                )
                audio_bytes = b"".join(audio_generator)
                audio_data = io.BytesIO(audio_bytes)
                pygame.mixer.music.load(audio_data)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy(): time.sleep(0.1)
            except Exception as e:
                print(f"❌ An error occurred during audio playback: {e}")
        self.speak_thread = threading.Thread(target=run_audio_playback)
        self.speak_thread.start()

    def stop_speaking(self):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            print("⏹️  Interrupting speech.")
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        if self.speak_thread and self.speak_thread.is_alive():
            self.speak_thread.join(timeout=0.5)

    def stop_listening(self):
        print("🛑 Stopping agent...")
        self.stop_listening_event.set()
        self.stop_speaking()

    def listen_and_respond(self):
        print("🎙️  Starting listening loop with offline model...")
        self.pyaudio_instance = pyaudio.PyAudio()
        self.pyaudio_stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16, channels=1, rate=16000,
            input=True, frames_per_buffer=4096 
        )
        self.pyaudio_stream.start_stream()
        print("🎤 Microphone is now open and listening!")
        
        try:
            while not self.stop_listening_event.is_set():
                data = self.pyaudio_stream.read(2048, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result_json = self.recognizer.Result()
                    result_dict = json.loads(result_json)
                    transcript = result_dict.get("text", "")
                    if transcript:
                        self._handle_final_transcript(transcript)

        except KeyboardInterrupt:
            self.stop_listening()
        except Exception as e:
            print(f"❌ An error occurred in listen loop: {e}")
        finally:
            print("🧹 Cleaning up resources...")
            if self.pyaudio_stream and self.pyaudio_stream.is_active():
                self.pyaudio_stream.stop_stream()
                self.pyaudio_stream.close()
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
            print("✅ Cleanup complete.")