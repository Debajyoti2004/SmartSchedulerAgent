import os
import json
from typing import Annotated, Sequence, TypedDict, List
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.messages.utils import get_buffer_string
from langgraph.graph.message import add_messages
from langchain_core.documents import Document
from .prompt import prompt
from langchain_community.vectorstores import FAISS
from .memory import get_vector_store, save_vector_store,embedding_model

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools import tools, tools_by_name

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    recall_memories: List[str]

llm = ChatCohere(
    cohere_api_key=os.getenv("COHERE_API_KEY"),
    model="command-r-plus",
    temperature=0
).bind_tools(tools=tools)

def get_user_id_from_config(config):
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id")
    if user_id is None:
        raise ValueError("User ID must be provided in the config.")
    return user_id

def get_session_id_from_config(config):
    configurable = config.get("configurable", {})
    session_id = configurable.get("thread_id")
    if session_id is None:
        raise ValueError("Session ID (thread_id) must be provided in the config.")
    return session_id

def add_conversation_to_memory(user_id: str, session_id: str, user_input: str, agent_response: str):
    vector_store = get_vector_store()
    documents = [
        Document(
            page_content=user_input,
            metadata={"user_id": user_id, "session_id": session_id, "speaker": "user"}
        ),
        Document(
            page_content=agent_response,
            metadata={"user_id": user_id, "session_id": session_id, "speaker": "agent"}
        )
    ]
    
    if vector_store is None:
        new_store = FAISS.from_documents(documents, embedding_model)
    else:
        vector_store.add_documents(documents)
        new_store = vector_store

    save_vector_store(new_store)


def load_memories(state: AgentState, config) -> dict:
    vector_store = get_vector_store()
    if vector_store is None:
        return {"recall_memories": []}
        
    user_id = get_user_id_from_config(config)
    session_id = get_session_id_from_config(config)

    if not state["messages"]:
        return {"recall_memories": []}
        
    convo_str = get_buffer_string(state["messages"])
    metadata_filter = {"user_id": user_id, "session_id": session_id}
    
    results = vector_store.similarity_search(
        query=convo_str,
        k=5,
        filter=metadata_filter
    )
    recall_memories = [doc.page_content for doc in results]
    return {"recall_memories": recall_memories}

def agent_node(state: AgentState, config) -> dict:
    recall_str = "\n".join(state["recall_memories"])
    final_prompt = prompt.format_messages(recall_memories=recall_str)
    all_messages = final_prompt + state["messages"]
    prediction = llm.invoke(all_messages, config)
    return {"messages": [prediction]}

def tool_node(state: AgentState, config) -> dict:
    outputs = []
    last_message = state["messages"][-1]

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"messages": []}

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        if tool_name in tools_by_name:
            tool_result = tools_by_name[tool_name].invoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result, ensure_ascii=False),
                    name=tool_name,
                    tool_call_id=tool_call.get("id"),
                )
            )
        else:
            outputs.append(
                ToolMessage(
                    content=f"Error: Tool '{tool_name}' not found.",
                    name=tool_name,
                    tool_call_id=tool_call.get("id"),
                )
            )
    return {"messages": outputs}

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return "end"
    else:
        return "continue"