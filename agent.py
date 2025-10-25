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

def get_agent_with_context(df: pd.DataFrame, column_descriptions: dict, dataset_context: str):
    """
    Create an agent that uses column descriptions instead of the full dataset
    
    Args:
        df: The pandas DataFrame (for code execution only)
        column_descriptions: Dictionary of column descriptions
        dataset_context: Formatted context string about the dataset
    """
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    sample_size = min(10, len(df))  # Only 10 rows max
    limited_df = df.head(sample_size)
    
    # Add basic statistics to the context
    stats_context = f"""
    {dataset_context}
    
    Sample Data (first {sample_size} rows):
    {limited_df.to_string()}
    
    Basic Statistics:
    {df.describe().to_string()}
    """
    
    # Create a custom prompt that includes our column descriptions
    from langchain.prompts import PromptTemplate
    
    # Create the prompt template with proper variables
    template = f"""
    You are a highly intelligent data scientist working with a dataset.

    {stats_context}

    You have access to a DataFrame named 'df' with the above structure and sample data.
    You can use the python_repl_ast tool to execute Python code on this data.

    Instructions:
    - Use the python_repl_ast tool to execute Python code for analysis
    - For visualizations, use matplotlib or seaborn with proper Streamlit integration
    - Always include plt.figure(figsize=(10,6)) and plt.tight_layout() for graphs
    - Use st.pyplot(plt) instead of plt.show() for Streamlit compatibility
    - Provide clear explanations of your findings
    - If a column is missing or an error occurs, explain the issue
    - IMPORTANT: You only have access to sample data, not the full dataset

    Question: {{input}}
    {{agent_scratchpad}}
    """
    
    prompt = PromptTemplate(
        input_variables=["input", "agent_scratchpad"],
        template=template
    )
    
    # Create the agent using the LIMITED dataset
    from langchain_experimental.agents import create_pandas_dataframe_agent
    
    agent = create_pandas_dataframe_agent(
        llm=llm,
        df=limited_df,
        prompt=prompt,
        verbose=True,
        allow_dangerous_code=True,
        max_iterations=15,
        max_execution_time=120,
        agent_type="openai-tools"
    )
    
    return agent

def get_agent(df: pd.DataFrame):
    """
    Legacy function - kept for backward compatibility
    Now creates an agent that uses column descriptions
    """
    from column_analyzer import ColumnAnalyzer
    
    # Analyze columns to get descriptions
    analyzer = ColumnAnalyzer()
    column_descriptions = analyzer.analyze_columns(df)
    dataset_context = analyzer.create_dataset_context(column_descriptions, df)
    
    return get_agent_with_context(df, column_descriptions, dataset_context)

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
