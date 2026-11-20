import os
import re
import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def get_code(question, columns):
    prompt = f"""You are a data analyst.
A pandas DataFrame named `df` has these columns: {columns}.
Question: {question}
Write pandas code that answers the question.
Store the final answer in a variable named `result`.
Return only code."""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


def clean_code(text):
    # Markdown backticks hata kar sirf code nikalta hai
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def run_code(code, df):
    scope = {"df": df, "pd": pd}
    exec(code, scope)
    return scope.get("result")


if __name__ == "__main__":
    df = pd.read_csv("data/titanic.csv")
    question = "What is the survival rate by passenger class?"

    raw = get_code(question, list(df.columns))
    code = clean_code(raw)

    print("Generated code:\n", code)
    print("\nResult:\n", run_code(code, df))