import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


from insight_gemini import generate_sql

st.set_page_config(page_title="Insight Query Interface", page_icon="🤖", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

st.title("Insight Query")
st.write("Ask me anything!")

file = st.file_uploader("Upload your data here")
if file:
    df = pd.read_csv(file)

    st.write(df)

    group_col = st.selectbox("Select a column to group by", df.columns)

    # Select column for values
    value_col = st.selectbox("Select a column for values", df.columns)

    if group_col and value_col:
        # Perform group by and aggregation
        grouped_data = df.groupby(group_col)[value_col].count()
        
        st.write("Grouped Data:")
        st.dataframe(grouped_data)

        width = st.slider("Chart Width", min_value=5, max_value=15, value=8)
        height = st.slider("Chart Height", min_value=5, max_value=15, value=6)

        # Create pie chart
        fig, ax = plt.subplots(figsize=(width, height))
        ax.pie(grouped_data, labels=grouped_data.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)


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
