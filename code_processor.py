import re
import sys
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from agent import validate_graph_code, validate_insights_code

def replace_plt_show_with_streamlit(code: str) -> str:
    """
    Replace plt.show() with st.pyplot(plt) in the generated code
    """
    # Replace plt.show() with st.pyplot(plt)
    code = re.sub(r'plt\.show\(\)', 'st.pyplot(plt)', code)
    
    # Also replace plt.show() with different spacing
    code = re.sub(r'plt\.show\( \)', 'st.pyplot(plt)', code)
    
    return code

class CodeProcessor:
    """Class to process and execute code returned by the agent"""
    
    def __init__(self, df):
        self.df = df
        self.globals_dict = {
            'df': df,
            'pd': pd,
            'plt': plt,
            'sns': sns,
            'st': st
        }
    
    def extract_code(self, response):
        """Extract Python code from the agent's response"""
        # Look for code blocks marked with ```
        code_pattern = r'```python\s*(.*?)\s*```'
        code_matches = re.findall(code_pattern, response, re.DOTALL)
        
        if not code_matches:
            # Look for code blocks without language specification
            code_pattern = r'```\s*(.*?)\s*```'
            code_matches = re.findall(code_pattern, response, re.DOTALL)
        
        return code_matches
    
    def detect_action_type(self, response):
        """Detect if the response is for insights or graph generation"""
        response_lower = response.lower()
        
        # Keywords for graph generation
        graph_keywords = [
            'plot', 'chart', 'graph', 'visualize', 'visualization', 
            'bar chart', 'line chart', 'scatter plot', 'histogram',
            'box plot', 'heatmap', 'pie chart', 'create a graph',
            'show me a', 'display a', 'generate a'
        ]
        
        # Keywords for insights
        insight_keywords = [
            'summary', 'describe', 'analyze', 'insights', 'statistics',
            'mean', 'average', 'count', 'missing', 'correlation',
            'trends', 'patterns', 'overview', 'information'
        ]
        
        # Check for graph keywords
        for keyword in graph_keywords:
            if keyword in response_lower:
                return "graph"
        
        # Check for insight keywords
        for keyword in insight_keywords:
            if keyword in response_lower:
                return "insights"
        
        # Default to insights if no clear indication
        return "insights"
    
    def execute_code(self, code, task_type="INSIGHTS_TASK"):
        """Execute the extracted code safely"""
        try:
            print("Original code:", code)
            
            # Replace plt.show() with st.pyplot(plt) before execution
            code = replace_plt_show_with_streamlit(code)
            
            print("Code after replacement:", code)
            
            # Validate code based on task type
            if task_type == "GRAPH_TASK":
                if not validate_graph_code(code):
                    return False, "Graph code missing required Streamlit elements", None
            else:
                if not validate_insights_code(code):
                    return False, "Insights code contains dangerous elements", None
            
            # Create a new namespace for execution
            local_dict = {}
            
            # Execute the code
            exec(code, self.globals_dict, local_dict)
            
            # If it's a graph, return the figure for display
            if task_type == "GRAPH_TASK":
                # Check if there's a current figure
                if plt.get_fignums():
                    fig = plt.gcf()
                    return True, "Code executed successfully", fig
                else:
                    return True, "Code executed successfully", None
            
            return True, "Code executed successfully", None
        except Exception as e:
            return False, f"Error executing code: {str(e)}", None
    
    def process_response(self, response):
        """Process the agent's response and determine action type"""
        action_type = self.detect_action_type(response)
        code_blocks = self.extract_code(response)
        
        return {
            'action_type': action_type,
            'code_blocks': code_blocks,
            'has_code': len(code_blocks) > 0,
            'original_response': response
        }