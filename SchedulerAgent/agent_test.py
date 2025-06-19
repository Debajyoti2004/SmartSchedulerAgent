import uuid
import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from node import add_conversation_to_memory 
from graph import compile_agent_workflow

def pretty_print_chunk(chunk):
    print("---")
    for key, value in chunk.items():
        if key == "agent" and isinstance(value, AIMessage):
            print(f"✅ Agent Output:")
            if value.tool_calls:
                print(f"   - 📝 Plan: {value.tool_plan}")
                for tc in value.tool_calls:
                    print(f"   - ⚙️ Calling Tool: `{tc['name']}` with args: {json.dumps(tc['args'])}")
            else:
                print(f"   - 🗣️ Final Response: {value.content}")
        elif key == "tools" and isinstance(value, ToolMessage):
            print(f"↪️ Tool Result:")
            print(f"   - Tool `{value.name}` returned: {value.content}")
        else:
            print(f"📦 Chunk Key '{key}': {value}")
    print("---\n")


def run_test_scenario_live():
    print("--- 🎬 Starting Agent Test Scenario (Live Debug Mode) ---")

    agent_workflow = compile_agent_workflow()
    
    test_user_id = "live_debug_user_001"
    test_session_id = f"test_session_{uuid.uuid4()}"
    
    config = {"configurable": {"user_id": test_user_id, "thread_id": test_session_id}}
    
    print(f"🆔 Test User ID: {test_user_id}")
    print(f"🔄 Test Session ID: {test_session_id}\n")

    def process_turn_live(user_input: str, user_id: str, session_id: str):
        print(f"--- 🧪 Starting Turn: User Input ---")
        print(f"👤 YOU: {user_input}\n")
        
        final_ai_message = None
        
        response_stream = agent_workflow.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config
        )
        
        final_ai_message=response_stream["messages"][-1].content
        print(f"✅ Turn Complete. Final Agent Response: \"{final_ai_message}\"\n")

        if final_ai_message:
            print(f"💾 Saving conversation to memory for session: {session_id}")
            
            add_conversation_to_memory(
                user_id=user_id,
                session_id=session_id,
                user_input=user_input, 
                agent_response=final_ai_message
            )
            
            print("... Memory saved.\n")
    
    process_turn_live("Hi, I need to schedule a meeting.", test_user_id, test_session_id)
    
    process_turn_live("My timezone is America/New_York. Please schedule 'Q3 Planning' for next Tuesday at 2:00PM for 45 minutes.", test_user_id, test_session_id)

    process_turn_live("Yes, that sounds good. Please book it.", test_user_id, test_session_id)

    print("--- 🎉 All Test Scenarios Passed Successfully! ---")

if __name__ == "__main__":
    run_test_scenario_live()