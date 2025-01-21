import streamlit as st

def bar_chart_plot(df):
    st.write("### Select Column for Bar Chart")

    index_column = st.selectbox("Select an index to plot", options=df.columns, index=4)

    value_column = st.selectbox("Select a column to plot", options=df.columns, index=5)

    if value_column:
        st.write(f"### Bar Chart for '{value_column}'")
        st.bar_chart(df.set_index(index_column)[value_column])
