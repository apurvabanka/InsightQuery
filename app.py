import streamlit as st
import pandas as pd
from agent import get_agent
from dotenv import load_dotenv
from code_processor import CodeProcessor
from callbacks import ThinkingCallbackHandler
import io
import sys
import re
import ast
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO

load_dotenv()

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "df" not in st.session_state:
    st.session_state.df = None

if "agent" not in st.session_state:
    st.session_state.agent = None

if "code_processor" not in st.session_state:
    st.session_state.code_processor = None

st.set_page_config(page_title="CSV Chat Assistant", layout="wide")
st.title("💬 CSV Chat Assistant")

# Sidebar for file upload
with st.sidebar:
    st.header("📁 Upload Your Data")
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    
    if uploaded_file:
        if st.session_state.df is None or st.button("🔄 Reload Data"):
            st.session_state.df = pd.read_csv(uploaded_file)
            st.session_state.agent = get_agent(st.session_state.df)
            st.session_state.code_processor = CodeProcessor(st.session_state.df)
            st.session_state.messages = []  # Clear chat history when new file is loaded
            st.success("✅ Data loaded successfully!")
        
        if st.session_state.df is not None:
            st.subheader("📊 Data Preview")
            st.dataframe(st.session_state.df.head())
            
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.rerun()

# Main chat area
if st.session_state.df is not None:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                # Show thinking first if available
                if "thinking" in message and message["thinking"]:
                    st.markdown("**🤔 Thinking:**")
                    st.markdown(message["thinking"])
                    st.markdown("---")
                
                # Display the complete response
                st.markdown("**🤖 Agent Response:**")
                st.write(message["content"])
                
                # Show code execution results if available
                if "code_result" in message and message["code_result"]:
                    with st.expander("🔧 Code Execution Result"):
                        st.write(message["code_result"])
                
                # Show graphs if generated
                if "graph_generated" in message and message["graph_generated"]:
                    st.success("📊 Graph generated successfully!")
                    # Display any saved graph figures
                    if "graph_figures" in message and message["graph_figures"]:
                        for i, fig in enumerate(message["graph_figures"]):
                            st.pyplot(fig)
                            plt.close(fig)  # Close after displaying in history

    # Chat input
    if prompt := st.chat_input("Ask a question about your data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            thinking_placeholder = st.empty()
            
            try:
                # Create callback handler for thinking
                callback_handler = ThinkingCallbackHandler(thinking_placeholder)
                
                # Show thinking process first
                thinking_placeholder.markdown("**🤔 Thinking:**")
                
                # Get response from agent
                response = st.session_state.agent.run(prompt, callbacks=[callback_handler])

                print("Agent response: ", response)
                
                # Add separator after thinking
                thinking_placeholder.markdown("---")
                
                # Display the complete agent response
                message_placeholder.markdown("**🤖 Agent Response:**")
                message_placeholder.markdown(response)
                message_placeholder.pyplot(plt.gcf())  # Display the plot
                plt.clf()  # Clean up for next round
                
                # Execute code if present (extract code from response)
                code_result = None
                graph_generated = False
                graph_figures = []
                
                # Extract code blocks from the response
                code_pattern = r'```python\s*(.*?)\s*```'
                code_matches = re.findall(code_pattern, response, re.DOTALL)

                print('Code Match Found: ', code_matches)
                
                if not code_matches:
                    # Look for code blocks without language specification
                    code_pattern = r'```\s*(.*?)\s*```'
                    code_matches = re.findall(code_pattern, response, re.DOTALL)
                
                # If no code blocks found, try to extract from dictionary format
                if not code_matches:
                    # Look for dictionary format with "query" key
                    dict_pattern = r'\{[^}]*"query"[^}]*\}'
                    dict_matches = re.findall(dict_pattern, response, re.DOTALL)
                    
                    print('Dict matches found: ', dict_matches)
                    
                    for dict_match in dict_matches:
                        try:
                            # Try to parse as JSON and extract query
                            import json
                            # Clean up the dict_match to make it valid JSON
                            cleaned_dict = dict_match.replace("'", '"')
                            parsed_dict = json.loads(cleaned_dict)
                            if 'query' in parsed_dict:
                                code_matches.append(parsed_dict['query'])
                                print('Extracted query: ', parsed_dict['query'])
                        except json.JSONDecodeError as e:
                            print('JSON decode error: ', e)
                            # If JSON parsing fails, try to extract query manually
                            query_match = re.search(r'"query":\s*"([^"]*)"', dict_match)
                            if query_match:
                                code_matches.append(query_match.group(1))
                                print('Manual extraction: ', query_match.group(1))
                
                if code_matches:
                    st.markdown("**🔧 Executing Code...**")
                    
                    # Execute the entire code as one block
                    full_code = "\n".join(code_matches)
                    
                    # Determine if it's a graph based on content
                    is_graph = any(keyword in full_code.lower() for keyword in 
                                 ['plt.', 'sns.', 'plot', 'chart', 'graph', 'figure', 'histogram', 'scatter', 'bar'])
                    
                    # Debug: Show what we're executing
                    st.markdown("**Complete Code to Execute:**")
                    st.code(full_code, language='python')
                    st.markdown(f"**Detected as graph:** {is_graph}")
                    
                    success, result, fig = st.session_state.code_processor.execute_code(
                        full_code, "GRAPH_TASK" if is_graph else "INSIGHTS_TASK"
                    )
                    
                    if success:
                        if is_graph and fig is not None:
                            graph_generated = True
                            graph_figures.append(fig)
                            st.success("📊 Graph generated successfully!")
                            # Display the graph immediately
                            st.pyplot(fig)
                            # Don't close the figure here, let it be displayed
                        else:
                            st.success("✅ Code executed successfully!")
                            if is_graph:
                                st.warning("⚠️ Graph code executed but no figure was created")
                    else:
                        st.error(f"❌ Code execution failed: {result}")
                    
                    code_result = result
                
                # Add assistant message to chat history
                thinking_text = "\n\n".join(callback_handler.thinking_steps) if callback_handler.thinking_steps else ""
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "thinking": thinking_text,
                    "code_result": code_result,
                    "graph_generated": graph_generated,
                    "graph_figures": graph_figures
                })
                
            except Exception as e:
                error_message = f"Error: {str(e)}"
                message_placeholder.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_message
                })

else:
    # Welcome message when no file is uploaded
    st.markdown("""
    ## 👋 Welcome to CSV Chat Assistant!
    
    **How to get started:**
    1. 📁 Upload your CSV file using the sidebar
    2. 💬 Start asking questions about your data
    3. 🤔 Watch the AI think through your questions
    4. 💡 Get insights and answers instantly
    5. 📊 Generate beautiful visualizations
    
    **Example questions you can ask:**
    - "What are the main trends in this data?"
    - "Show me the average values for each column"
    - "Which rows have missing values?"
    - "Create a summary of the data"
    - "Plot a bar chart of the sales data"
    - "Generate a scatter plot of x vs y"
    - "Show me a histogram of the age distribution"
    """)
    
    # Placeholder for chat interface
    st.chat_message("assistant").write("Hi! I'm your CSV assistant. Please upload a CSV file to get started! 🚀")
