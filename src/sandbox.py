import ast
import io
import json
import os
import subprocess
import sys
import tempfile

import pandas as pd

TIMEOUT_SECONDS = 20

BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "socket", "shutil", "pathlib", "requests",
    "urllib", "http", "ctypes", "importlib", "pickle", "builtins", "io",
}
BLOCKED_CALLS = {
    "exec", "eval", "open", "compile", "__import__", "input", "globals",
    "locals", "getattr", "setattr", "delattr", "vars", "breakpoint",
}
BLOCKED_ATTRS = {
    "read_csv", "read_excel", "read_pickle", "read_json", "read_html",
    "read_sql", "read_parquet", "to_csv", "to_excel", "to_pickle",
    "to_json", "to_parquet", "to_sql", "os", "sys", "io", "system",
    "popen", "compat",
}

RUNNER = """
import sys, json
import pandas as pd

df = pd.read_pickle(sys.argv[1])
scope = {"df": df, "pd": pd}
exec(open(sys.argv[2], encoding="utf-8").read(), scope)
r = scope.get("result")
if isinstance(r, pd.Series):
    r = r.to_frame()
if isinstance(r, pd.DataFrame):
    out = {"type": "table", "data": r.to_json(orient="split")}
else:
    out = {"type": "text", "data": str(r)}
print("@@RESULT@@" + json.dumps(out))
"""


def check_code(code):
    """Khatarnak code chalne se pehle pakadta hai."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            names = []
        for name in names:
            if name.split(".")[0] in BLOCKED_IMPORTS:
                raise ValueError(f"Blocked import: {name}")

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in BLOCKED_CALLS
        ):
            raise ValueError(f"Blocked function: {node.func.id}")

        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__") or node.attr in BLOCKED_ATTRS:
                raise ValueError(f"Blocked attribute: {node.attr}")


def run_code_safe(code, df):
    check_code(code)

    with tempfile.TemporaryDirectory() as tmp:
        df_path = os.path.join(tmp, "data.pkl")
        code_path = os.path.join(tmp, "code.py")
        runner_path = os.path.join(tmp, "runner.py")

        df.to_pickle(df_path)
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code)
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(RUNNER)

        # Minimal environment: API key aur baaki secrets child ko nahi milte
        env = {"SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}

        try:
            proc = subprocess.run(
                [sys.executable, "-I", runner_path, df_path, code_path],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Code {TIMEOUT_SECONDS}s se zyada chala, roka gaya.")

    if proc.returncode != 0:
        last_lines = "\n".join(proc.stderr.strip().splitlines()[-5:])
        raise RuntimeError(last_lines or "Code fail hua.")

    for line in proc.stdout.splitlines():
        if line.startswith("@@RESULT@@"):
            out = json.loads(line[len("@@RESULT@@"):])
            if out["type"] == "table":
                return pd.read_json(io.StringIO(out["data"]), orient="split")
            return out["data"]

    raise RuntimeError("Code ne `result` variable set nahi kiya.")