import pandas as pd
import streamlit as st

from bar_chart import bar_chart_plot
from data_cleaning import data_cleaning_process
from insight_gemini import generate_sql
from load_spark import load_data_to_spark
from pie_chart import pie_chart_plot

st.set_page_config(page_title="Insight Query Interface", page_icon="🤖", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

st.title("Insight Query!!!")
st.write("Ask me anything!")

file = st.file_uploader("Upload your data here")
if file:
    df = pd.read_csv(file)

    st.write(df)

    # load_data_to_spark(file)

    df = data_cleaning_process(df)

    col1, col2 = st.columns(2)

    with col1:
        pie_chart_plot(df)
    with col2:
        bar_chart_plot(df)

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message:", "")
    submitted = st.form_submit_button("Send")

    if submitted and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        response = generate_sql(str(st.session_state.messages[-1]))
        st.session_state.messages.append({"role": "assistant", "content": response})

for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
    elif message["role"] == "assistant":
        st.markdown(f"**Response:** {message['content']}")

if st.button("Clear Chat"):
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]
