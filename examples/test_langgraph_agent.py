#!/usr/bin/env python3
"""LangGraph agent test with LLM and tool nodes for Agent Spy tracing."""

import os
from datetime import datetime
from typing import Annotated, Literal, TypedDict

# Configure LangChain tracing for Agent Spy
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "http://localhost:8000/api/v1"
os.environ["LANGSMITH_API_KEY"] = "test-key"
os.environ["LANGSMITH_PROJECT"] = "langgraph-agent-test"

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode


# Define the clock tool
@tool
def get_current_time() -> str:
    """Get the current system time. Use this when asked about the current time or 'what time is it'."""
    current_time = datetime.now()
    return f"The current time is {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"


# Define the state for our graph
class AgentState(TypedDict):
    messages: Annotated[list, "The list of messages in the conversation"]


# Create the LLM with tool binding
def create_llm():
    """Create and configure the LLM with tools."""
    llm = ChatOllama(model="qwen3:8b", base_url="http://aurora.local:11434", temperature=0.1)

    # Bind the tool to the LLM
    tools = [get_current_time]
    llm_with_tools = llm.bind_tools(tools)
    return llm_with_tools


# Define the LLM node
def llm_node(state: AgentState):
    """LLM node that can decide to use tools or end the conversation."""
    llm = create_llm()
    response = llm.invoke(state["messages"])

    # Add the response to messages
    return {"messages": [response]}


# Define routing logic
def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Determine if we should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]

    # If the last message has tool calls, go to tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    # Otherwise, we're done
    return "end"


def create_agent_graph():
    """Create the LangGraph agent."""
    print("🔧 Creating LangGraph agent...")

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("llm", llm_node)
    workflow.add_node("tools", ToolNode([get_current_time]))

    # Add edges
    workflow.add_edge(START, "llm")
    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )
    workflow.add_edge("tools", "llm")

    # Compile the graph
    app = workflow.compile()

    print("✅ LangGraph agent created successfully!")
    return app


def main():
    """Main function to test the LangGraph agent."""
    print("🚀 Testing LangGraph Agent with Agent Spy Tracing")
    print("=" * 50)
    print("🌐 Ollama server: aurora.local:11434")
    print("🤖 Model: qwen3:8b")
    print("🔧 Tracing: Agent Spy (localhost:8000)")
    print("🛠️ Tool: get_current_time")
    print()

    try:
        # Create the agent
        agent = create_agent_graph()

        # Test the agent with a time-related question
        print("📝 Testing agent with: 'What time is it now?'")
        print()

        initial_state = {"messages": [HumanMessage(content="What time is it now?")]}

        print("🔄 Running agent...")
        result = agent.invoke(initial_state)

        print("✅ Agent execution completed!")
        print()
        print("📋 Final messages:")
        for i, message in enumerate(result["messages"], 1):
            print(f"  {i}. {type(message).__name__}: {message.content[:100]}...")

        print()
        print("🎉 LangGraph agent test completed successfully!")
        print("📊 Check the Agent Spy server logs to see the detailed trace hierarchy:")
        print("   - Initial LLM call")
        print("   - Tool invocation")
        print("   - Follow-up LLM call")
        print("   - Final response")

    except Exception as e:
        print(f"❌ Error running LangGraph agent: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
