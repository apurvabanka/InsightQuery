import os
import re

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

def generate_sql(prompt):
    response = model.generate_content(
        "Generate SQL for "+  prompt
    ) 

    response_sql = extract_sql_code(response.text)

    return response_sql

def extract_sql_code(text):
    pattern = r"```sql\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches
