import re
import pandas as pd

from llm import generate


def get_code(question, columns):
    prompt = f"""You are a data analyst.
A pandas DataFrame named `df` has these columns: {columns}.
Question: {question}
Write pandas code that answers the question.
Store the final answer in a variable named `result`.
Return only code."""
    return generate(prompt)


def clean_code(text):
    # Markdown backticks hata kar sirf code nikalta hai
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def run_code(code, df):
    scope = {"df": df, "pd": pd}
    exec(code, scope)
    return scope.get("result")


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "data/titanic.csv"
    df = pd.read_csv(path)
    print(f"Dataset load hua: {df.shape[0]} rows, {df.shape[1]} columns")
    print("Columns:", list(df.columns))

    while True:
        question = input("\nSawaal puchhiye (band karne ke liye 'exit'): ")
        if question.strip().lower() == "exit":
            break

        code = clean_code(get_code(question, list(df.columns)))
        print("\nGenerated code:\n", code)
        print("\nResult:\n", run_code(code, df))