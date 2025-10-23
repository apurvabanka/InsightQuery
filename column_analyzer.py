import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import json
from typing import Dict, List, Any

class ColumnAnalyzer:
    """Analyzes CSV columns and generates descriptions using LLM"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
    def analyze_columns(self, df: pd.DataFrame, sample_size: int = 10) -> Dict[str, str]:
        """
        Analyze each column and generate descriptions using LLM
        
        Args:
            df: The pandas DataFrame to analyze
            sample_size: Number of sample values to send to LLM for each column
            
        Returns:
            Dictionary mapping column names to their descriptions
        """
        column_descriptions = {}
        
        # Get sample data for analysis
        sample_df = df.head(sample_size)
        
        for column in df.columns:
            try:
                # Get column info
                column_info = {
                    'name': column,
                    'dtype': str(df[column].dtype),
                    'sample_values': sample_df[column].dropna().head(5).tolist(),
                    'null_count': df[column].isnull().sum(),
                    'unique_count': df[column].nunique(),
                    'total_rows': len(df)
                }
                
                # Generate description using LLM
                description = self._generate_column_description(column_info)
                column_descriptions[column] = description
                
            except Exception as e:
                print(f"Error analyzing column {column}: {str(e)}")
                column_descriptions[column] = f"Column {column} (analysis failed)"
        
        return column_descriptions
    
    def _generate_column_description(self, column_info: Dict[str, Any]) -> str:
        """Generate a description for a single column using LLM"""
        
        prompt_template = """
        Analyze the following column information and provide a clear, concise description of what this column represents.

        Column Information:
        - Name: {column_name}
        - Data Type: {dtype}
        - Sample Values: {sample_values}
        - Null Values: {null_count} out of {total_rows}
        - Unique Values: {unique_count}

        Please provide a brief description (1-2 sentences) of what this column represents based on the sample data and column name.
        Focus on the business meaning and data content, not technical details.
        """
        
        prompt = PromptTemplate(
            input_variables=["column_name", "dtype", "sample_values", "null_count", "total_rows", "unique_count"],
            template=prompt_template
        )
        
        try:
            response = self.llm.invoke(prompt.format(
                column_name=column_info['name'],
                dtype=column_info['dtype'],
                sample_values=column_info['sample_values'],
                null_count=column_info['null_count'],
                total_rows=column_info['total_rows'],
                unique_count=column_info['unique_count']
            ))
            
            return response.content.strip()
            
        except Exception as e:
            print(f"Error generating description for {column_info['name']}: {str(e)}")
            return f"Column {column_info['name']} with {column_info['dtype']} data type"
    
    def create_dataset_context(self, column_descriptions: Dict[str, str], df: pd.DataFrame) -> str:
        """
        Create a context string with column descriptions and basic dataset info
        
        Args:
            column_descriptions: Dictionary of column descriptions
            df: The original DataFrame
            
        Returns:
            Formatted context string for the agent
        """
        context = f"""
        Dataset Overview:
        - Total rows: {len(df)}
        - Total columns: {len(df.columns)}
        
        Column Descriptions:
        """
        
        for column, description in column_descriptions.items():
            context += f"\n- {column}: {description}"
        
        context += f"""
        
        You have access to a DataFrame named 'df' with the above structure. 
        You can use pandas operations to analyze this data, but remember you're working with the full dataset.
        """
        
        return context
