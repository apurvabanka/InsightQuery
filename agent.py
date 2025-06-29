from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import OutputParserException
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
import pandas as pd
import json

# Define ENUM for task types
# class TaskType(str, Enum):
#     INSIGHTS_TASK = "INSIGHTS_TASK"
#     GRAPH_TASK = "GRAPH_TASK"

# Single unified task model
# class TaskResponse(BaseModel):
#     """Unified model for both insights and graph tasks"""
#     task_type: TaskType = Field(description="Type of task (INSIGHTS_TASK or GRAPH_TASK)")
#     explanation: str = Field(description="Clear explanation of findings or what the graph shows")
#     code: Optional[str] = Field(default=None, description="Python code for calculations or visualization")
#     summary: Optional[str] = Field(default=None, description="Brief summary of key insights (for insights tasks)")
#     recommendations: Optional[List[str]] = Field(default=None, description="List of recommendations based on analysis (for insights tasks)")
#     graph_type: Optional[str] = Field(default=None, description="Type of graph (bar, line, scatter, histogram, etc.) (for graph tasks)")
#     title: Optional[str] = Field(default=None, description="Title for the graph (for graph tasks)")
#     x_label: Optional[str] = Field(default=None, description="X-axis label (for graph tasks)")
#     y_label: Optional[str] = Field(default=None, description="Y-axis label (for graph tasks)")

def get_agent(df: pd.DataFrame):
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Generate schema string
    # schema = ", ".join(df.columns)
    
    # Create output parser
    # parser = PydanticOutputParser(pydantic_object=TaskResponse)
    
    # Define the template string with placeholders
    # template = """
    # You are a highly intelligent data scientist.
    # You are working with a DataFrame named `df`.
    
    # The DataFrame has the following columns: {schema}
    
    # You are only allowed to use the tool named "python_repl_ast" to execute Python code.
    # Do not invent tool names or actions.

    # IMPORTANT: You have two types of tasks with strict output formats:
    
    # 1. INSIGHTS_TASK: When asked for analysis, summary, statistics, or insights:
    #    - Use the python_repl_ast tool to calculate statistics
    #    - Return structured output with explanation, code, summary, and recommendations
    
    # 2. GRAPH_TASK: When asked to create plots, charts, or visualizations:
    #    - Generate Python code using matplotlib or seaborn
    #    - ALWAYS include these lines in your graph code:
    #      * plt.figure(figsize=(10,6))  # Set figure size
    #      * plt.tight_layout()  # Adjust layout
    #      * st.pyplot(plt)  # Display in Streamlit (NOT plt.show())
    #    - IMPORTANT: When generating visualizations using matplotlib:
    #      * Do NOT use `plt.show()`
    #      * Instead, use `st.pyplot(plt)`
    #      * This is because you are working in a Streamlit environment
    #    - Return structured output with explanation, code, graph_type, title, and labels
    
    # Instructions:
    # - First, think through the steps to solve the problem
    # - Then, call the tool "python_repl_ast" with the correct Python code
    # - If a column is missing or an error occurs, explain the issue without retrying
    # - For graphs, ALWAYS use: plt.figure(figsize=(10,6)), plt.tight_layout(), and st.pyplot(plt)
    # - For insights, provide clear explanations with supporting data
    
    # IMPORTANT: You MUST return your response in the following JSON format:
    # {format_instructions}
    
    # Question: {input}
    # """
    
    # Create the prompt with expected input variables
    # custom_prompt = PromptTemplate(
    #     input_variables=["schema", "input", "format_instructions"],
    #     template=template
    # )
    
    # Pass the prompt as a formatted string by setting partial_variables
    return create_pandas_dataframe_agent(
        llm=llm,
        df=df,  # Use the limited dataframe
        # prompt=custom_prompt.partial(schema=schema, format_instructions=parser.get_format_instructions()),  # this fills the schema
        verbose=True,
        allow_dangerous_code=True,
        max_iterations=15,
        max_execution_time=120,
        agent_type="openai-tools"  # Use the correct agent type
    )

# def parse_agent_response(response: str) -> TaskResponse:
#     """
#     Parse the agent response and return structured task object
#     """
#     try:
#         # Try to parse as JSON first
#         if response.strip().startswith('{'):
#             return TaskResponse.parse_raw(response)
#         else:
#             # If not JSON, try to extract JSON from the response
#             import re
#             json_match = re.search(r'\{.*\}', response, re.DOTALL)
#             if json_match:
#                 json_str = json_match.group()
#                 return TaskResponse.parse_raw(json_str)
#             else:
#                 raise OutputParserException("No valid JSON found in response")
#     except Exception as e:
#         # Fallback: create a basic insights task
#         return TaskResponse(
#             task_type=TaskType.INSIGHTS_TASK,
#             explanation=response,
#             summary="Analysis completed",
#             recommendations=["Review the data for patterns", "Consider additional analysis"]
#         )

def validate_graph_code(code: str) -> bool:
    """
    Validate that graph code contains required Streamlit elements
    """
    required_elements = [
        'plt.figure(figsize=(10,6))',
        'plt.tight_layout()',
        'st.pyplot('  # More flexible - just check for st.pyplot call
    ]
    
    code_lower = code.lower()
    for element in required_elements:
        if element not in code_lower:
            return False
    return True

def validate_insights_code(code: str) -> bool:
    """
    Validate that insights code is safe and appropriate
    """
    dangerous_keywords = ['exec', 'eval', 'open', 'file', 'system', 'subprocess']
    code_lower = code.lower()
    
    for keyword in dangerous_keywords:
        if keyword in code_lower:
            return False
    return True
