import streamlit as st
import matplotlib.pyplot as plt

def pie_chart_plot(df):   
    group_col = st.selectbox("Select a column to group by", df.columns, index=8)

    value_col = st.selectbox("Select a column for values", df.columns, index=0)

    if group_col and value_col:
        grouped_data = df.groupby(group_col)[value_col].count()

        with st.expander("Grouped Data:"):
            st.dataframe(grouped_data)

        fig, ax = plt.subplots(figsize=(2, 2))
        ax.pie(grouped_data, labels=grouped_data.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)
