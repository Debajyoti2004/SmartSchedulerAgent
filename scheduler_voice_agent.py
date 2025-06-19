import os
import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig 

from SchedulerAgent import (
    add_conversation_to_memory,
    compile_agent_workflow
)

load_dotenv()

class SchedulerAgentVoice:
    def __init__(self, user_id: str, user_name: str, use_tts: bool = True):
        self.user_id = user_id
        self.user_name = user_name
        self.use_tts = use_tts
        self.scheduler_agent = compile_agent_workflow()

        if use_tts:
            self.tts_engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

    def speak(self, text: str):
        print(f"\n🤖 AGENT: {text}")
        if self.use_tts:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()

    def listen(self) -> Optional[str]:
        with self.microphone as source:
            print("\n🎤 Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio_data = self.recognizer.listen(source, timeout=12, phrase_time_limit=20)
                print("🔎 Transcribing...")
                command = self.recognizer.recognize_google(audio_data)
                print(f"👤 YOU: {command}")
                return command
            except sr.WaitTimeoutError:
                print("⚠️ Listening timed out.")
                return None
            except sr.UnknownValueError:
                self.speak("Sorry, I couldn’t catch that.")
                return None
            except Exception as e:
                print(f"❌ Audio service error: {e}")
                self.speak("Sorry, I'm having trouble with audio.")
                return None

    def get_agent_response(
        self, session_id: str, user_text: str
    ) -> Dict[str, Union[List[str], str]]:
        config = RunnableConfig(
            configurable={
                "user_id": self.user_id,
                "thread_id": session_id
            }
        )

        try:
            response = self.scheduler_agent.invoke(
                input={"messages": [HumanMessage(content=user_text)]},
                config=config,
                stream_mode="values"
            )
        except Exception as e:
            print(f"❌ Agent invocation failed: {e}")
            return {"thoughts": ["Agent failed to respond."], "final_response": "Sorry, there was an error."}

        messages = response.get("messages", [])
        thoughts = [msg.content for msg in messages[:-1]] if len(messages) > 1 else []
        final_response = messages[-1].content if messages else "No response from agent."

        add_conversation_to_memory(
            user_id=self.user_id,
            session_id=session_id,
            user_input=user_text,
            agent_response=final_response
        )

        return {"thoughts": thoughts, "final_response": final_response}

    def process_input(self, session_id: str, user_text: str):
        response_data = self.get_agent_response(session_id, user_text)
        thoughts = response_data["thoughts"]
        final_response = response_data["final_response"]
        return thoughts, final_response

if __name__ == "__main__":
    agent = SchedulerAgentVoice(user_id="test_user_001", user_name="Debajyoti", use_tts=False)
    session_id = "session_test_001"
    user_input = "My current time zone is Asia/Kolkata.Set a meeting with John next Monday at 10 AM"
    thoughts, final_response = agent.process_input(session_id=session_id, user_text=user_input)
    for idx, thought in enumerate(thoughts, 1):
        print(f"Thought {idx}: {thought}")
    print(f"Final Response: {final_response}")
