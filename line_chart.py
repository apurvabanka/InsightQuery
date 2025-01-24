import streamlit as st
import plotly.express as px

def line_chart_pyplot(df):
    st.write("### Line Chart")

    columns_to_plot = st.multiselect(
        "Select Columns to Plot",
        options=df.columns[1:],
        default=df.columns[1]
    )

    # Filter data based on user selection
    if columns_to_plot:
        # Plot line chart with Plotly
        fig = px.line(df, x="Outlet_Establishment_Year", y=columns_to_plot, title="Line Chart")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select at least one column to plot.")