import pandas as pd
import json
from typing import Dict, Any, List, Tuple
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import HumanMessage, SystemMessage
from crud.csv_crud import CSVFileCRUD
from sqlalchemy.orm import Session
from schemas.chat_schema import RequestType
from dotenv import load_dotenv

load_dotenv()

class ChatService:
    def __init__(self):

        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.1,
        )
        
    def classify_request(self, user_message: str) -> str:
        """Classify if the user is asking for an insight or a graph"""
        
        # Get allowed states from Pydantic enum
        allowed_states = [state.value for state in RequestType]
        allowed_states_str = ' or '.join(allowed_states)
        
        classification_prompt = PromptTemplate(
            input_variables=["user_message", "allowed_states", "allowed_states_str"],
            template="""
            Analyze the following user message and classify it as either {allowed_states_str}.
            
            User message: {user_message}
            
            Allowed classification states: {allowed_states}
            
            Classification rules:
            - If the user is asking for analysis, trends, patterns, insights, or understanding of the data → "insight"
            - If the user is asking for a chart, graph, visualization, plot, or visual representation → "graph"
            
            Respond with only one of the allowed states: {allowed_states_str}
            """
        )
        
        try:
            response = self.llm.invoke(classification_prompt.format(
                user_message=user_message,
                allowed_states=allowed_states,
                allowed_states_str=allowed_states_str
            ))
            classification = response.content.strip().lower()
            
            # Validate that the classification is one of the allowed states
            if classification in allowed_states:
                return classification
            else:
                # If classification is not valid, default to insight
                return "insight"
        except Exception as e:
            # Default to insight if classification fails
            return "insight"
    
    def load_csv_data(self, db: Session, session_id: str) -> pd.DataFrame:
        """Load CSV data for a given session"""
        csv_files = CSVFileCRUD.get_files_by_session(db, session_id)
        
        if not csv_files:
            raise ValueError(f"No CSV files found for session {session_id}")
        
        # For now, use the first CSV file. In the future, you might want to merge multiple files
        csv_file = csv_files[0]
        
        try:
            df = pd.read_csv(csv_file.file_path, delimiter=",")
            print(df.head())
            return df
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")
    
    def generate_insight(self, df: pd.DataFrame, user_message: str) -> Dict[str, Any]:
        """Generate insights from CSV data using SQL queries"""
        
        # Create a comprehensive summary of the data
        data_summary = f"""
            Dataset Summary:
            - Shape: {df.shape}
            - Columns: {list(df.columns)}
            - Data types: {df.dtypes.to_dict()}
            - Numeric columns: {df.select_dtypes(include=['number']).columns.tolist()}
            - Categorical columns: {df.select_dtypes(include=['object']).columns.tolist()}
        """
        
        # First, generate SQL query based on user message
        sql_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert SQL analyst. Based on the user's question, generate a SQL query to analyze the data.

            Available columns: {columns}
            
            Generate a SQL query that will answer the user's question. The query should:
            1. Have valid SQL syntax
            2. Use the actual column names from the dataset
            3. Return meaningful results for analysis
            4. Include appropriate aggregations (COUNT, SUM, AVG, etc.) when needed
            5. Include WHERE clauses for filtering when relevant
            
            Return only the SQL query, no explanations or additional text. Use df as the table name when generating the SQL. 
            Return only the SQL and do not enclose it with quotes in the beginning or the end."""),
            HumanMessage(content=f"""Dataset Summary:
            {data_summary}

            User Question: {user_message}

            Generate a SQL query to answer this question:""")
        ])
        
        try:
            # Generate SQL query
            sql_chain = sql_prompt | self.llm
            sql_response = sql_chain.invoke({
                'data_summary': data_summary,
                'user_message': user_message,
                'columns': list(df.columns)
            })
            
            sql_query = sql_response.content.strip()
            print(f"Generated SQL: {sql_query}")
            
            # Execute SQL on the DataFrame
            query_result = self._execute_sql_on_dataframe(df, sql_query)
            
            # Generate insights based on the SQL results
            insight_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert data analyst. Based on the SQL query results, provide specific, data-driven insights.

                Response format (valid JSON only):
                {{
                    "message": "Direct answer to the user's question with specific data points",
                    "insights": [
                        "Insight 1: [specific finding with numbers/percentages]",
                        "Insight 2: [specific finding with numbers/percentages]", 
                        "Insight 3: [specific finding with numbers/percentages]"
                    ],
                    "summary": "Brief summary of the most important findings",
                    "sql_query": "The SQL query that was executed"
                }}

                Use the actual query results provided, not examples."""),
                HumanMessage(content=f"""User Question: {user_message}

                SQL Query Executed: {sql_query}

                Query Results:
                {query_result}

                Analyze these results and provide specific insights based on the User Question.""")
            ])
            
            insight_chain = insight_prompt | self.llm | JsonOutputParser()
            
            response = insight_chain.invoke({
                'user_message': user_message,
                'sql_query': sql_query,
                'query_results': str(query_result)
            })

            print("Generated insight:", response)
            
            # Validate response structure
            if not isinstance(response, dict):
                raise ValueError("Response is not a dictionary")
            
            required_keys = ['message', 'insights', 'summary']
            for key in required_keys:
                if key not in response:
                    raise ValueError(f"Missing required key: {key}")
            
            # Validate that insights are not placeholder text
            insights = response.get('insights', [])
            if not insights or any('[insert' in str(insight) for insight in insights):
                raise ValueError("Response contains placeholder text")
            
            # Add SQL query to response
            response['sql_query'] = sql_query
            
            return response
        except Exception as e:
            print(f"Error in generate_insight: {str(e)}")
            return {
                "message": "An error occurred while analyzing the data",
                "insights": [f"Error: {str(e)}"],
                "summary": "Unable to generate insights due to an error",
                "sql_query": "N/A"
            }
    
    def _execute_sql_on_dataframe(self, df: pd.DataFrame, sql_query: str) -> pd.DataFrame:
        """Execute SQL query on a pandas DataFrame using pandasql"""
        try:
            # Import pandasql for SQL execution on DataFrames
            from pandasql import sqldf
            
            # Create a local namespace with the DataFrame
            locals_dict = {'df': df}
            
            # Execute the SQL query
            result = sqldf(sql_query, locals_dict)
            
            return result
        except ImportError:
            # Fallback to pandas query if pandasql is not available
            print("pandasql not available, using pandas query fallback")
            return self._fallback_sql_execution(df, sql_query)
        except Exception as e:
            print(f"Error executing SQL: {str(e)}")
            # Return empty DataFrame with error message
            return pd.DataFrame({'error': [f"SQL execution error: {str(e)}"]})
    
    def _fallback_sql_execution(self, df: pd.DataFrame, sql_query: str) -> pd.DataFrame:
        """Fallback method to execute SQL-like operations using pandas"""
        try:
            # Simple fallback for basic SQL operations
            sql_lower = sql_query.lower().strip()
            
            if sql_lower.startswith('select'):
                # Handle basic SELECT queries
                if 'count(*)' in sql_lower:
                    return pd.DataFrame({'count': [len(df)]})
                elif 'avg(' in sql_lower or 'average(' in sql_lower:
                    # Extract column name from AVG function
                    import re
                    match = re.search(r'avg\((\w+)\)', sql_lower)
                    if match:
                        col_name = match.group(1)
                        if col_name in df.columns:
                            return pd.DataFrame({'avg': [df[col_name].mean()]})
                elif 'sum(' in sql_lower:
                    # Extract column name from SUM function
                    import re
                    match = re.search(r'sum\((\w+)\)', sql_lower)
                    if match:
                        col_name = match.group(1)
                        if col_name in df.columns:
                            return pd.DataFrame({'sum': df[col_name].sum()})
                else:
                    # Return first few rows as fallback
                    return df.head(10)
            
            # Default fallback
            return df.head(5)
            
        except Exception as e:
            print(f"Fallback SQL execution error: {str(e)}")
            return pd.DataFrame({'error': [f"Fallback execution error: {str(e)}"]})
    
    def generate_graph(self, df: pd.DataFrame, user_message: str) -> Dict[str, Any]:
        """Generate graph configuration from CSV data"""
        
        # Create a summary of the data
        data_summary = f"""
        Dataset Summary:
        - Shape: {df.shape}
        - Columns: {list(df.columns)}
        - Data types: {df.dtypes.to_dict()}
        - Numeric columns: {df.select_dtypes(include=['number']).columns.tolist()}
        - Categorical columns: {df.select_dtypes(include=['object']).columns.tolist()}
        """
        
        graph_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a data visualization expert. Based on the dataset summary and user request, suggest the best chart type and provide the configuration.

            Please provide a JSON response with:
            1. The most appropriate chart type (bar, line, scatter, pie, histogram, etc.)
            2. The data to be plotted
            3. Chart configuration (title, labels, colors, etc.)

            Available chart types: bar, line, scatter, pie, histogram, box, heatmap

            Format your response as JSON:
            {{
                "chart_type": "chart_type",
                "chart_data": {{
                    "x": "column_name or data",
                    "y": "column_name or data",
                    "title": "Chart title"
                }},
                "chart_config": {{
                    "xlabel": "X-axis label",
                    "ylabel": "Y-axis label",
                    "color": "color_scheme"
                }}
            }}"""),
            HumanMessage(content="""Dataset Summary:
{data_summary}

User Request: {user_message}""")
        ])
        
        try:
            chain = graph_prompt | self.llm | JsonOutputParser()

            result = chain.invoke({
                'data_summary': data_summary,
                'user_message': user_message
            })
            
            # Add actual data based on the suggested configuration
            chart_data = self._prepare_chart_data(df, result)
            result["chart_data"] = chart_data
            
            return result
        except Exception as e:
            return {
                "chart_type": "bar",
                "chart_data": {"error": f"Error generating graph: {str(e)}"},
                "chart_config": {"title": "Error", "xlabel": "", "ylabel": ""}
            }
    
    def _prepare_chart_data(self, df: pd.DataFrame, graph_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare actual chart data based on the graph configuration"""
        try:
            chart_type = graph_config.get("chart_type", "bar")
            chart_data = graph_config.get("chart_data", {})
            
            if chart_type == "bar":
                # For bar charts, we need categorical x and numeric y
                x_col = chart_data.get("x")
                y_col = chart_data.get("y")
                
                if x_col and y_col and x_col in df.columns and y_col in df.columns:
                    data = df.groupby(x_col)[y_col].mean().reset_index()
                    return {
                        "x": data[x_col].tolist(),
                        "y": data[y_col].tolist(),
                        "title": chart_data.get("title", f"{y_col} by {x_col}")
                    }
            
            elif chart_type == "line":
                # For line charts, we need a time series or sequential data
                x_col = chart_data.get("x")
                y_col = chart_data.get("y")
                
                if x_col and y_col and x_col in df.columns and y_col in df.columns:
                    data = df.sort_values(x_col)
                    return {
                        "x": data[x_col].tolist(),
                        "y": data[y_col].tolist(),
                        "title": chart_data.get("title", f"{y_col} over {x_col}")
                    }
            
            elif chart_type == "scatter":
                # For scatter plots, we need two numeric columns
                x_col = chart_data.get("x")
                y_col = chart_data.get("y")
                
                if x_col and y_col and x_col in df.columns and y_col in df.columns:
                    return {
                        "x": df[x_col].tolist(),
                        "y": df[y_col].tolist(),
                        "title": chart_data.get("title", f"{y_col} vs {x_col}")
                    }
            
            elif chart_type == "pie":
                # For pie charts, we need categorical data
                x_col = chart_data.get("x")
                
                if x_col and x_col in df.columns:
                    data = df[x_col].value_counts()
                    return {
                        "labels": data.index.tolist(),
                        "values": data.values.tolist(),
                        "title": chart_data.get("title", f"Distribution of {x_col}")
                    }
            
            # Default fallback
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) >= 2:
                return {
                    "x": df[numeric_cols[0]].tolist(),
                    "y": df[numeric_cols[1]].tolist(),
                    "title": f"{numeric_cols[1]} vs {numeric_cols[0]}"
                }
            
            return {"error": "Unable to prepare chart data"}
            
        except Exception as e:
            return {"error": f"Error preparing chart data: {str(e)}"}
    
    def process_chat(self, db: Session, session_id: str, user_message: str) -> Dict[str, Any]:
        """Main method to process chat requests"""
        try:
            # Classify the request
            request_type = self.classify_request(user_message)
            
            # Load CSV data
            df = self.load_csv_data(db, session_id)
            
            if request_type == "insight":
                result = self.generate_insight(df, user_message)
                return {
                    "request_type": "insight",
                    "message": result.get("message", "Analysis completed"),
                    "data": {
                        "insights": result.get("insights", []),
                        "summary": result.get("summary", ""),
                        "sql_query": result.get("sql_query", "N/A")
                    }
                }
            else:  # graph
                result = self.generate_graph(df, user_message)
                return {
                    "request_type": "graph",
                    "message": f"Generated {result.get('chart_type', 'chart')} based on your request",
                    "data": {
                        "chart_type": result.get("chart_type", "bar"),
                        "chart_data": result.get("chart_data", {}),
                        "chart_config": result.get("chart_config", {})
                    }
                }
                
        except Exception as e:
            return {
                "request_type": "error",
                "message": "An error occurred while processing your request",
                "error": str(e)
            } 