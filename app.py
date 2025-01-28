import pandas as pd
import streamlit as st

from bar_chart import bar_chart_plot
from data_cleaning import data_cleaning_process
from insight_gemini import generate_sql
from line_chart import line_chart_pyplot
from pie_chart import pie_chart_plot
from utils import create_vector_embeddings

st.set_page_config(page_title="Insight Query Interface", page_icon="🤖", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help?"}]

st.title("Insight Query!!!")
st.write("Ask me anything!")

file = st.file_uploader("Upload your data here")

df = None
chain = None

if file:
    df = pd.read_csv(file)

    chain = create_vector_embeddings(df)

user_input = st.chat_input()

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    response = chain.invoke(user_input)
    st.session_state.messages.append({"role": "assistant", "content": response})

for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").write(message['content'])
    elif message["role"] == "assistant":
        with st.chat_message('assistant'):
            st.write(f"**Response:** {message['content']}")
