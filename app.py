import streamlit as st
import pandas as pd
from agent import get_agent
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="CSV Insight App", layout="centered")
st.title("🔍 Ask Questions About Your CSV")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head())

    question = st.text_input("Ask a question about your data:")
    
    if st.button("Ask") and question:
        with st.spinner("Thinking..."):
            try:
                agent = get_agent(df)
                answer = agent.run(question)
                st.success(answer)
            except Exception as e:
                st.error(f"Error: {str(e)}")
