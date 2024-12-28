import streamlit as st

from insight_gemini import generate_sql

st.set_page_config(page_title="Insight Query Interface", page_icon="🤖", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

# Title and description
st.title("Insight Query")
st.write("Ask me anything!")

# User input
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

# Option to clear chat
if st.button("Clear Chat"):
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]
