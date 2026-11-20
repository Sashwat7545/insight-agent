import os
import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

df = pd.read_csv("data/titanic.csv")
columns = list(df.columns)
question = "What is the survival rate by passenger class?"

prompt = f"""You are a data analyst.
A pandas DataFrame named `df` has these columns: {columns}.
Question: {question}
Write the pandas code that answers the question. Return only code."""

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt,
)
print(response.text)