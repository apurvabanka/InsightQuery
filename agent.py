from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

import pandas as pd

def get_agent(df: pd.DataFrame):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        verbose=False,
        allow_dangerous_code=False
    )
