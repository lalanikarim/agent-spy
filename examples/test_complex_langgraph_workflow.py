#!/usr/bin/env python3
"""
Complex LangGraph Workflow Example for Agent Spy

This example demonstrates a sophisticated multi-step pipeline:
1. Prompt Template -> formats initial input
2. LLM -> processes formatted prompt
3. Output Parser -> extracts key information
4. LLM -> refines and expands the information
5. Output Parser -> structures the refined content
6. LLM with Structured Output -> creates final structured response
7. Output Parser -> validates and formats final output

This creates a deep trace hierarchy perfect for testing Agent Spy's dashboard.
"""

import os
from datetime import datetime
from typing import Any, TypedDict

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

# Configure LangChain tracing to Agent Spy
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "http://localhost:8000/api/v1"
os.environ["LANGCHAIN_API_KEY"] = "test-key"
os.environ["LANGCHAIN_PROJECT"] = "ComplexWorkflow"

# Initialize Ollama LLM
llm = ChatOllama(model="qwen3:8b", base_url="http://aurora.local:11434", temperature=0.7)


# Define the structured output schema
class PersonAnalysis(BaseModel):
    """Structured analysis of a person"""

    name: str = Field(description="Full name of the person")
    profession: str = Field(description="Primary profession or role")
    key_achievements: list[str] = Field(description="List of major achievements")
    personality_traits: list[str] = Field(description="Key personality characteristics")
    historical_significance: str = Field(description="Why this person is historically significant")
    time_period: str = Field(description="Time period when they lived/were active")
    legacy_impact: str = Field(description="How they impacted future generations")


class WorkflowState(TypedDict):
    """State that flows through the workflow"""

    original_input: str
    formatted_prompt: str
    initial_response: str
    extracted_info: str
    refined_analysis: str
    structured_content: dict[str, Any]
    final_analysis: PersonAnalysis
    validation_result: str


# Step 1: Prompt Template Node
def prompt_template_node(state: WorkflowState) -> WorkflowState:
    """Format the initial input using a prompt template"""
    template = PromptTemplate(
        input_variables=["person"],
        template="""
        You are a historical researcher. Please provide a comprehensive overview of {person}.

        Focus on:
        - Their background and early life
        - Major achievements and contributions
        - Impact on their field or society
        - Personal characteristics and leadership style

        Provide a detailed but concise response suitable for further analysis.
        """,
    )

    formatted = template.format(person=state["original_input"])
    state["formatted_prompt"] = formatted
    return state


# Step 2: First LLM Node
def first_llm_node(state: WorkflowState) -> WorkflowState:
    """Process the formatted prompt with the first LLM call"""
    response = llm.invoke(state["formatted_prompt"])
    state["initial_response"] = response.content
    return state


# Step 3: First Output Parser Node
def first_parser_node(state: WorkflowState) -> WorkflowState:
    """Extract key information from the initial LLM response"""
    extraction_prompt = f"""
    From the following text about a historical figure, extract the most important information:

    {state['initial_response']}

    Focus on extracting:
    - Key facts and dates
    - Major accomplishments
    - Character traits
    - Historical context

    Present this as a structured summary.
    """

    parser = StrOutputParser()
    extracted = llm.invoke(extraction_prompt)
    state["extracted_info"] = parser.parse(extracted)
    return state


# Step 4: Second LLM Node
def second_llm_node(state: WorkflowState) -> WorkflowState:
    """Refine and expand the extracted information"""
    refinement_prompt = f"""
    Based on this extracted information about a historical figure:

    {state['extracted_info']}

    Please refine and expand this into a more comprehensive analysis. Add:
    - Additional context about their historical period
    - Analysis of their leadership style and decision-making
    - Discussion of controversies or challenges they faced
    - Assessment of their long-term impact and legacy

    Make this analysis scholarly but accessible.
    """

    response = llm.invoke(refinement_prompt)
    state["refined_analysis"] = response.content
    return state


# Step 5: Second Output Parser Node
def second_parser_node(state: WorkflowState) -> WorkflowState:
    """Structure the refined analysis into organized content"""
    structuring_prompt = f"""
    Convert the following analysis into a structured format with clear sections:

    {state['refined_analysis']}

    Organize into these sections:
    - Biography Summary
    - Major Achievements
    - Leadership Characteristics
    - Historical Impact
    - Legacy Assessment

    Return as a JSON object with these section names as keys.
    """

    parser = JsonOutputParser()
    structured = llm.invoke(structuring_prompt)

    try:
        parsed_content = parser.parse(structured)
        state["structured_content"] = parsed_content
    except Exception as e:
        # Fallback if JSON parsing fails
        state["structured_content"] = {"raw_content": structured.content, "parse_error": str(e)}

    return state


# Step 6: Structured Output LLM Node
def structured_llm_node(state: WorkflowState) -> WorkflowState:
    """Generate final structured output using Pydantic model"""
    # Create a structured LLM that will output PersonAnalysis
    structured_llm = llm.with_structured_output(PersonAnalysis)

    final_prompt = f"""
    Based on all the previous analysis, create a comprehensive structured analysis:

    Original Analysis: {state['initial_response']}

    Extracted Information: {state['extracted_info']}

    Refined Analysis: {state['refined_analysis']}

    Structured Content: {state['structured_content']}

    Create a final comprehensive analysis with all required fields filled out accurately.
    """

    try:
        structured_output = structured_llm.invoke(final_prompt)
        state["final_analysis"] = structured_output
    except Exception as e:
        # Fallback PersonAnalysis if structured output fails
        state["final_analysis"] = PersonAnalysis(
            name="Analysis Failed",
            profession="Unknown",
            key_achievements=["Could not parse structured output"],
            personality_traits=["Error in processing"],
            historical_significance=f"Structured output error: {str(e)}",
            time_period="Unknown",
            legacy_impact="Processing failed",
        )

    return state


# Step 7: Final Output Parser Node
def final_parser_node(state: WorkflowState) -> WorkflowState:
    """Validate and format the final structured output"""
    analysis = state["final_analysis"]

    validation_prompt = f"""
    Review this structured analysis for completeness and accuracy:

    Name: {analysis.name}
    Profession: {analysis.profession}
    Achievements: {analysis.key_achievements}
    Traits: {analysis.personality_traits}
    Significance: {analysis.historical_significance}
    Time Period: {analysis.time_period}
    Legacy: {analysis.legacy_impact}

    Provide a brief validation summary indicating:
    - Completeness of information
    - Accuracy assessment
    - Overall quality rating
    """

    validation = llm.invoke(validation_prompt)
    parser = StrOutputParser()
    state["validation_result"] = parser.parse(validation)

    return state


# Build the workflow graph
def create_complex_workflow():
    """Create the complex multi-step workflow"""
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("prompt_template", prompt_template_node)
    workflow.add_node("first_llm", first_llm_node)
    workflow.add_node("first_parser", first_parser_node)
    workflow.add_node("second_llm", second_llm_node)
    workflow.add_node("second_parser", second_parser_node)
    workflow.add_node("structured_llm", structured_llm_node)
    workflow.add_node("final_parser", final_parser_node)

    # Define the linear flow
    workflow.set_entry_point("prompt_template")
    workflow.add_edge("prompt_template", "first_llm")
    workflow.add_edge("first_llm", "first_parser")
    workflow.add_edge("first_parser", "second_llm")
    workflow.add_edge("second_llm", "second_parser")
    workflow.add_edge("second_parser", "structured_llm")
    workflow.add_edge("structured_llm", "final_parser")
    workflow.add_edge("final_parser", END)

    return workflow.compile()


def main():
    """Run the complex workflow example"""
    print("🚀 Starting Complex LangGraph Workflow Example")
    print("=" * 60)

    # Create the workflow
    app = create_complex_workflow()

    # Test with a historical figure
    test_input = "Leonardo da Vinci"

    print(f"📝 Analyzing: {test_input}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🔄 Processing through 7-step pipeline...")
    print("   1. Prompt Template")
    print("   2. First LLM Call")
    print("   3. First Output Parser")
    print("   4. Second LLM Call")
    print("   5. Second Output Parser")
    print("   6. Structured Output LLM")
    print("   7. Final Output Parser")
    print()

    # Initialize state
    initial_state = {
        "original_input": test_input,
        "formatted_prompt": "",
        "initial_response": "",
        "extracted_info": "",
        "refined_analysis": "",
        "structured_content": {},
        "final_analysis": None,
        "validation_result": "",
    }

    try:
        # Run the workflow
        result = app.invoke(initial_state)

        print("✅ Workflow completed successfully!")
        print("=" * 60)
        print("\n📊 FINAL RESULTS:")
        print("-" * 30)

        final_analysis = result["final_analysis"]
        print(f"👤 Name: {final_analysis.name}")
        print(f"💼 Profession: {final_analysis.profession}")
        print(f"📅 Time Period: {final_analysis.time_period}")
        print("🏆 Key Achievements:")
        for achievement in final_analysis.key_achievements[:3]:  # Show first 3
            print(f"   • {achievement}")
        print("🧠 Personality Traits:")
        for trait in final_analysis.personality_traits[:3]:  # Show first 3
            print(f"   • {trait}")
        print("⭐ Historical Significance:")
        print(f"   {final_analysis.historical_significance[:200]}...")
        print("🌟 Legacy Impact:")
        print(f"   {final_analysis.legacy_impact[:200]}...")

        print("\n🔍 Validation Summary:")
        validation_text = (
            result["validation_result"] if isinstance(result["validation_result"], str) else str(result["validation_result"])
        )
        print(f"   {validation_text[:300]}...")

        print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n🎯 Check Agent Spy dashboard for detailed trace hierarchy!")
        print("   http://localhost:3000")

    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
