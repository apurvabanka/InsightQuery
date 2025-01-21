import time
import streamlit as st

def data_cleaning_process(df):
    
    st.write("### Performing Data Cleaning")
    progress = st.progress(0)

    df = df.fillna(0)

    for i in range(101):
        time.sleep(0.01)
        progress.progress(i)
    


    st.success("Cleaning completed!")

    return df
