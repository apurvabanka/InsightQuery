import time

import streamlit as st
from pyspark.sql import SparkSession

def load_data_to_spark(file):

    st.write("### Loading data to Spark")
    progress = st.progress(0)


    for i in range(101):
        time.sleep(0.01)
        progress.progress(i)

    spark = SparkSession.builder \
        .master("local[*]") \
        .appName("LoadCSV") \
        .getOrCreate()

    # Load CSV file into DataFrame
    df = spark.read.csv(file.name, header=True, inferSchema=True) 

    return df
