
from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .node import (
    AgentState, 
    load_memories, 
    agent_node, 
    tool_node, 
    should_continue
)

compiled_scheduler_agent_graph = None
def compile_agent_workflow():
    global compiled_scheduler_agent_graph

    if compiled_scheduler_agent_graph is not None:
        print("Response agent workflow already compiled. Returning existing instance.")
        return compiled_scheduler_agent_graph

    builder = StateGraph(AgentState)
    builder.add_node("load_memories", load_memories)
    builder.add_node("Scheduler_Agent", agent_node)
    builder.add_node("Agent_Tools", tool_node)

    builder.add_edge(START, "load_memories")
    builder.add_edge("load_memories", "Scheduler_Agent")
    
    builder.add_conditional_edges(
        "Scheduler_Agent",
        should_continue,
        {
            "continue": "Agent_Tools",
            "end": END
        }
    )
    
    builder.add_edge("Agent_Tools", "Scheduler_Agent")

    memory = MemorySaver()
    compiled_scheduler_agent_graph = builder.compile(checkpointer=memory)
    return compiled_scheduler_agent_graph
