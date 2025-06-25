# import time
# import threading
# from scheduler_voice_agent import SchedulerAgent

# def test_initialization():
#     """Tests if the agent class can be initialized without errors."""
#     print("--- 1. Testing Agent Initialization ---")
#     try:
#         agent = SchedulerAgent(
#             user_id="init_test",
#             user_name="TestUser",
#             use_tts=False  # No need for audio in this test
#         )
#         assert agent is not None
#         print("✅ PASSED: Agent initialized successfully.\n")
#         return True
#     except Exception as e:
#         print(f"❌ FAILED: Agent initialization failed: {e}\n")
#         return False

# def test_get_agent_response():
#     """Tests the core logic of getting a response from the agent."""
#     print("--- 2. Testing get_agent_response() ---")
#     agent = SchedulerAgent(user_id="response_test", user_name="TestUser", use_tts=False)
#     user_input = "Hello, what is your purpose?"
#     print(f"   Input: '{user_input}'")
    
#     try:
#         thoughts, final_response = agent.get_agent_response("session_123", user_input)
#         print(f"   Thoughts: {thoughts}")
#         print(f"   Final Response: {final_response}")
        
#         assert isinstance(thoughts, list)
#         assert isinstance(final_response, str) and final_response
#         print("✅ PASSED: Received a valid response from the agent.\n")
#         return True
#     except Exception as e:
#         print(f"❌ FAILED: get_agent_response() raised an exception: {e}\n")
#         return False

# def test_speak_and_stop():
#     """Tests the TTS speech and interruption functionality."""
#     print("--- 3. Testing speak() and stop_speaking() ---")
#     agent = SchedulerAgent(user_id="speak_test", user_name="TestUser", use_tts=True)
#     text_to_speak = "This is a test of the text to speech system. I will be interrupted shortly."
    
#     try:
#         print("   Starting to speak. You should hear audio now...")
#         agent.speak(text_to_speak)
#         time.sleep(3) # Let it speak for 3 seconds

#         print("   Interrupting speech...")
#         agent.stop_speaking()
        
#         # The thread should be stopped now.
#         time.sleep(0.5) # Give a moment for the thread to terminate
#         assert not agent.speak_thread.is_alive()
#         print("✅ PASSED: Speech was started and successfully interrupted.\n")
#         return True
#     except Exception as e:
#         print(f"❌ FAILED: Speaking/stopping test failed: {e}\n")
#         return False

# def test_full_listen_loop():
#     """Runs the full interactive listening loop for a short duration."""
#     print("--- 4. Testing Full Interactive Loop (15 seconds) ---")
#     agent = SchedulerAgent(user_id="full_loop_test", user_name="TestUser", use_tts=True)
    
#     # Run the main listening loop in a separate thread so we can stop it.
#     listen_thread = threading.Thread(target=agent.listen_and_respond)
    
#     try:
#         listen_thread.start()
#         print("\n🎙️  Speak into your microphone now! This test will automatically stop in 15 seconds.\n")
        
#         # Wait for 15 seconds
#         listen_thread.join(timeout=15)
        
#         print("\n   15-second test period over. Stopping agent...")
#         agent.stop_listening()
        
#         # Give the thread a moment to clean up and exit
#         listen_thread.join(timeout=2)
        
#         assert not listen_thread.is_alive()
#         print("✅ PASSED: Full interactive loop ran and shut down correctly.\n")
#         return True
#     except Exception as e:
#         print(f"❌ FAILED: Full listen loop test failed: {e}\n")
#         return False

# if __name__ == "__main__":
#     print("=========================================")
#     print("   Running Comprehensive Agent Tests")
#     print("=========================================\n")

#     # Run each test sequentially
#     # test_initialization()
#     # test_get_agent_response()
#     # test_speak_and_stop()
#     test_full_listen_loop()

#     print("=========================================")
#     print("          All Tests Complete")
#     print("=========================================")

# # from elevenlabs.client import ElevenLabs
# # import os
# # from dotenv import load_dotenv
# # load_dotenv()

# # client = ElevenLabs(
# #   api_key=os.getenv("ELEVENLABS_API_KEY"),
# # )

# # response = client.voices.search()
# # print(response.voices)
import pyaudio
import os
import json
import vosk
import audioop # Built-in Python library to work with audio data
import time

# --- Configuration ---
MODEL_PATH = "model"
SAMPLE_RATE = 16000
FRAMES_PER_BUFFER = 2048 # Use a smaller buffer for lower latency
VOLUME_THRESHOLD = 300 # RMS volume threshold to detect speech

# --- Verify Model Path ---
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"❌ Vosk model not found at path: '{MODEL_PATH}'.")

# --- Load the Vosk Model ---
print("▶️  Loading offline Vosk model...")
try:
    model = vosk.Model(MODEL_PATH)
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    recognizer.SetWords(False)
    print("✅ Model loaded successfully.")
except Exception as e:
    raise RuntimeError(f"❌ Failed to load Vosk model: {e}")

# --- Open Microphone Stream ---
print("\n▶️  Opening microphone stream...")
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER
)
stream.start_stream()
print("✅ Microphone is open.")
print("\n--- DETAILED MICROPHONE TEST ---")

# --- Main Listening Loop ---
try:
    while True:
        # Read a chunk of audio
        data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
        
        # Calculate the volume (RMS) of the audio chunk
        # The '2' is for 16-bit audio (2 bytes per sample)
        rms = audioop.rms(data, 2)

        # Print the live volume level. This is our key diagnostic.
        # The `\r` and `end=''` make it update on a single line.
        print(f"🎤 Live Volume (RMS): {rms:<5} ", end='\r')

        # Only process audio if it's above a certain volume
        if rms > VOLUME_THRESHOLD:
            if recognizer.AcceptWaveform(data):
                result_json = recognizer.Result()
                result_dict = json.loads(result_json)
                transcript = result_dict.get("text", "")
                if transcript:
                    # Clear the volume line and print the transcript
                    print(f"\n✅ You said: {transcript}")
        
        # Add a tiny sleep to prevent the loop from overwhelming the CPU
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n⏹️  Interrupted by user.")
finally:
    # --- Clean up resources ---
    print("\n🧹 Cleaning up resources...")
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("✅ Cleanup complete.")