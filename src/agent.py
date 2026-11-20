from llm import generate
from run_query import clean_code, run_code

MAX_ATTEMPTS = 3


def build_prompt(question, df, previous_code=None, error=None):
    prompt = f"""You are a data analyst.
A pandas DataFrame named `df` is already loaded. Do not read any files.
Columns and dtypes:
{df.dtypes.to_string()}

First 3 rows:
{df.head(3).to_string()}

Question: {question}

Rules:
- Write pandas code only. Do not import os, sys, subprocess or similar modules.
- Store the final answer in a variable named `result`.
- Return only code."""

    if previous_code and error:
        prompt += f"""

Your previous code failed.
Previous code:
{previous_code}

Error:
{error}

Fix the code and return only the corrected code."""
    return prompt


def answer_question(question, df):
    log = []
    code, error = None, None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        prompt = build_prompt(question, df, code, error)
        code = clean_code(generate(prompt))

        try:
            result = run_code(code, df)
            log.append({"attempt": attempt, "code": code, "error": None})
            print(f"[agent] attempt {attempt}: success")
            return {
                "success": True,
                "result": result,
                "code": code,
                "attempts": attempt,
                "log": log,
            }
        except Exception as e:
            error = str(e)
            log.append({"attempt": attempt, "code": code, "error": error})
            print(f"[agent] attempt {attempt}: failed -> {error}")

    return {
        "success": False,
        "result": None,
        "code": code,
        "attempts": MAX_ATTEMPTS,
        "log": log,
    }