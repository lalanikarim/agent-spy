#!/usr/bin/env python3
"""
Dual Chain LangGraph Agent Example for Agent Spy

This example demonstrates a LangGraph agent with two nodes, each calling
a separate LLM chain (Prompt Template → LLM → Output Parser).

Architecture:
- Agent with 2 nodes: content_analyzer and style_critic
- Each node has its own LLM chain with prompt template and output parser
- Creates parallel processing paths for comprehensive text analysis
- Perfect for testing Agent Spy's trace hierarchy visualization

Use case: Analyzing a piece of text from both content and style perspectives.
"""

import os
from datetime import datetime
from typing import TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

# Configure LangChain tracing to Agent Spy
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "http://localhost:8000/api/v1")
os.environ["LANGSMITH_API_KEY"] = "test-key"
os.environ["LANGSMITH_PROJECT"] = "DualChainAgent"

# Debug: Print environment variables to verify they're set
print("🔧 Environment variables:")
print(f"  LANGSMITH_TRACING: {os.environ.get('LANGSMITH_TRACING')}")
print(f"  LANGSMITH_ENDPOINT: {os.environ.get('LANGSMITH_ENDPOINT')}")
print(f"  LANGSMITH_PROJECT: {os.environ.get('LANGSMITH_PROJECT')}")
print(f"  OLLAMA_HOST: {os.getenv('OLLAMA_HOST', 'http://localhost:11434')}")

# Also try clearing LangSmith cache if available
try:
    from langsmith import utils

    utils.get_env_var.cache_clear()
    print("  ✅ Cleared LangSmith environment variable cache")
except ImportError:
    print("  ⚠️ LangSmith utils not available (cache not cleared)")

# Initialize Ollama LLM
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
llm = ChatOllama(model="qwen3:0.6b", base_url=ollama_host, temperature=0.7)


# Define the agent state
class AgentState(TypedDict):
    """State that flows through the agent"""

    input_text: str
    content_analysis: str
    style_analysis: str
    final_summary: str


# ================================
# LLM Chain 1: Content Analysis
# ================================


def create_content_analysis_chain():
    """Create the first LLM chain for content analysis"""

    # Prompt Template for content analysis
    content_prompt = PromptTemplate(
        input_variables=["text"],
        template="""
        You are a content analyst. Analyze the following text for its content and meaning:

        Text: {text}

        Please provide a comprehensive content analysis covering:
        1. Main themes and topics
        2. Key arguments or points made
        3. Facts, data, or evidence presented
        4. Logical structure and flow
        5. Target audience and purpose
        6. Strengths and weaknesses of the content

        Be thorough and objective in your analysis.
        """,
    )

    # Output Parser for content analysis
    content_parser = StrOutputParser()

    # Create the chain: Prompt → LLM → Parser
    content_chain = content_prompt | llm | content_parser

    return content_chain


# ================================
# LLM Chain 2: Style Analysis
# ================================


def create_style_analysis_chain():
    """Create the second LLM chain for style analysis"""

    # Prompt Template for style analysis
    style_prompt = PromptTemplate(
        input_variables=["text"],
        template="""
        You are a writing style critic. Analyze the following text for its style and presentation:

        Text: {text}

        Please provide a detailed style analysis covering:
        1. Writing tone and voice (formal, casual, academic, etc.)
        2. Sentence structure and complexity
        3. Vocabulary choice and word usage
        4. Clarity and readability
        5. Rhetorical devices and techniques used
        6. Overall writing quality and effectiveness
        7. Suggestions for improvement

        Focus on the HOW rather than the WHAT of the writing.
        """,
    )

    # Output Parser for style analysis
    style_parser = StrOutputParser()

    # Create the chain: Prompt → LLM → Parser
    style_chain = style_prompt | llm | style_parser

    return style_chain


# ================================
# Agent Nodes
# ================================


def content_analyzer_node(state: AgentState) -> AgentState:
    """First agent node: Analyzes content using the first LLM chain"""
    print("🔍 Content Analyzer Node: Starting content analysis...")

    # Create and invoke the content analysis chain
    content_chain = create_content_analysis_chain()

    try:
        content_analysis = content_chain.invoke({"text": state["input_text"]})
        state["content_analysis"] = content_analysis
        print("✅ Content analysis completed")
    except Exception as e:
        print(f"❌ Content analysis failed: {e}")
        state["content_analysis"] = f"Content analysis failed: {str(e)}"

    return state


def style_critic_node(state: AgentState) -> AgentState:
    """Second agent node: Analyzes style using the second LLM chain"""
    print("✍️  Style Critic Node: Starting style analysis...")

    # Create and invoke the style analysis chain
    style_chain = create_style_analysis_chain()

    try:
        style_analysis = style_chain.invoke({"text": state["input_text"]})
        state["style_analysis"] = style_analysis
        print("✅ Style analysis completed")
    except Exception as e:
        print(f"❌ Style analysis failed: {e}")
        state["style_analysis"] = f"Style analysis failed: {str(e)}"

    return state


def summarizer_node(state: AgentState) -> AgentState:
    """Final node: Creates a summary combining both analyses"""
    print("📋 Summarizer Node: Creating final summary...")

    # Create a summary prompt that combines both analyses
    summary_prompt = PromptTemplate(
        input_variables=["content_analysis", "style_analysis"],
        template="""
        Based on the following content and style analyses, create a comprehensive summary:

        CONTENT ANALYSIS:
        {content_analysis}

        STYLE ANALYSIS:
        {style_analysis}

        Please provide:
        1. A brief overview combining both perspectives
        2. Key strengths identified in both content and style
        3. Areas for improvement from both analyses
        4. Overall assessment and recommendations

        Keep the summary concise but comprehensive.
        """,
    )

    # Create summary chain
    summary_parser = StrOutputParser()
    summary_chain = summary_prompt | llm | summary_parser

    try:
        final_summary = summary_chain.invoke(
            {"content_analysis": state["content_analysis"], "style_analysis": state["style_analysis"]}
        )
        state["final_summary"] = final_summary
        print("✅ Final summary completed")
    except Exception as e:
        print(f"❌ Summary creation failed: {e}")
        state["final_summary"] = f"Summary creation failed: {str(e)}"

    return state


# ================================
# Agent Graph Construction
# ================================


def create_dual_chain_agent():
    """Create the LangGraph agent with two parallel analysis nodes"""

    # Create the state graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("content_analyzer", content_analyzer_node)
    workflow.add_node("style_critic", style_critic_node)
    workflow.add_node("summarizer", summarizer_node)

    # Set entry point
    workflow.set_entry_point("content_analyzer")

    # Define edges - both analyses run in sequence, then summarizer
    workflow.add_edge("content_analyzer", "style_critic")
    workflow.add_edge("style_critic", "summarizer")
    workflow.add_edge("summarizer", END)

    # Compile the workflow
    return workflow.compile()


# ================================
# Alternative: Parallel Execution
# ================================


def create_parallel_dual_chain_agent():
    """Create agent with parallel execution of both chains"""

    def parallel_analysis_node(state: AgentState) -> AgentState:
        """Node that runs both analyses in parallel (conceptually)"""
        print("🔄 Running parallel analysis...")

        # Run content analysis
        content_chain = create_content_analysis_chain()
        content_analysis = content_chain.invoke({"text": state["input_text"]})
        state["content_analysis"] = content_analysis

        # Run style analysis
        style_chain = create_style_analysis_chain()
        style_analysis = style_chain.invoke({"text": state["input_text"]})
        state["style_analysis"] = style_analysis

        print("✅ Parallel analysis completed")
        return state

    # Create simpler workflow
    workflow = StateGraph(AgentState)
    workflow.add_node("parallel_analyzer", parallel_analysis_node)
    workflow.add_node("summarizer", summarizer_node)

    workflow.set_entry_point("parallel_analyzer")
    workflow.add_edge("parallel_analyzer", "summarizer")
    workflow.add_edge("summarizer", END)

    return workflow.compile()


# ================================
# Main Execution
# ================================


def main():
    """Run the dual chain agent example"""
    print("🚀 Starting Dual Chain LangGraph Agent Example")
    print("=" * 60)

    # Sample text to analyze
    sample_text = """
    Artificial Intelligence represents one of the most transformative technologies of our time.
    However, its rapid development raises important questions about ethics, employment, and social impact.
    While AI can automate routine tasks and enhance human capabilities, we must carefully consider
    the implications for privacy, bias, and human autonomy. The challenge lies not just in creating
    more powerful AI systems, but in ensuring they serve humanity's best interests.
    """

    print("📝 Text to analyze:")
    print(f'"{sample_text.strip()}"')
    print()

    # Create the agent
    print("🏗️  Creating dual chain agent...")
    agent = create_dual_chain_agent()

    # Initialize state
    initial_state = {"input_text": sample_text.strip(), "content_analysis": "", "style_analysis": "", "final_summary": ""}

    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🔄 Running agent with two LLM chains...")
    print("   Node 1: Content Analyzer (Prompt → LLM → Parser)")
    print("   Node 2: Style Critic (Prompt → LLM → Parser)")
    print("   Node 3: Summarizer (Combines both analyses)")
    print()

    try:
        # Run the agent
        result = agent.invoke(initial_state)

        print("✅ Agent execution completed successfully!")
        print("=" * 60)
        print("\n📊 ANALYSIS RESULTS:")
        print("-" * 30)

        print("\n🔍 CONTENT ANALYSIS:")
        print("-" * 20)
        content_preview = result["content_analysis"][:400]
        print(f"{content_preview}...")

        print("\n✍️  STYLE ANALYSIS:")
        print("-" * 20)
        style_preview = result["style_analysis"][:400]
        print(f"{style_preview}...")

        print("\n📋 FINAL SUMMARY:")
        print("-" * 20)
        summary_preview = result["final_summary"][:500]
        print(f"{summary_preview}...")

        print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n🎯 Check Agent Spy dashboard for detailed trace hierarchy!")
        print("   http://localhost:3000")
        print("\n📈 Expected trace structure:")
        print("   └── DualChainAgent (root)")
        print("       ├── Content Analyzer Node")
        print("       │   ├── Prompt Template")
        print("       │   ├── LLM Call")
        print("       │   └── Output Parser")
        print("       ├── Style Critic Node")
        print("       │   ├── Prompt Template")
        print("       │   ├── LLM Call")
        print("       │   └── Output Parser")
        print("       └── Summarizer Node")
        print("           ├── Prompt Template")
        print("           ├── LLM Call")
        print("           └── Output Parser")

    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        import traceback

        traceback.print_exc()


def demo_parallel_version():
    """Demonstrate the parallel version of the agent"""
    print("\n" + "=" * 60)
    print("🔄 BONUS: Running Parallel Version")
    print("=" * 60)

    sample_text = "The future of work will be shaped by automation and human creativity working together."

    agent = create_parallel_dual_chain_agent()

    initial_state = {"input_text": sample_text, "content_analysis": "", "style_analysis": "", "final_summary": ""}

    try:
        agent.invoke(initial_state)
        print("✅ Parallel agent completed!")
        print("🎯 This creates a different trace pattern - check the dashboard!")

    except Exception as e:
        print(f"❌ Parallel agent failed: {e}")


if __name__ == "__main__":
    main()

    # Uncomment to also run the parallel version
    # demo_parallel_version()
