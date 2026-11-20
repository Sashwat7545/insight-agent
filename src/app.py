import pandas as pd
import streamlit as st

from agent import answer_question
from file_qa import ask_about_file

TABULAR = ("csv", "xlsx")
MEDIA = ("jpg", "jpeg", "png", "pdf")

st.set_page_config(page_title="InsightAgent", page_icon="📊", layout="wide")
st.title("📊 InsightAgent")
st.caption("Upload a CSV, Excel, image or PDF and ask questions in plain English.")


def load_data(file):
    if file.name.lower().endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


with st.sidebar:
    st.header("File")
    uploaded = st.file_uploader("Choose a file", type=list(TABULAR + MEDIA))

if uploaded is None:
    st.info("Upload a file in the sidebar to begin.")
    st.stop()

ext = uploaded.name.rsplit(".", 1)[-1].lower()
is_tabular = ext in TABULAR

# Reset chat when a new file is uploaded
if st.session_state.get("file_name") != uploaded.name:
    st.session_state.file_name = uploaded.name
    st.session_state.messages = []

# Preview
if is_tabular:
    df = load_data(uploaded)
    with st.sidebar:
        st.success(f"{df.shape[0]} rows, {df.shape[1]} columns")
        st.write("**Columns:**", list(df.columns))
    with st.expander("Dataset preview (first 5 rows)"):
        st.dataframe(df.head())
else:
    file_bytes = uploaded.getvalue()
    if ext in ("jpg", "jpeg", "png"):
        st.image(file_bytes, caption=uploaded.name, width=400)
    else:
        st.info(f"PDF loaded: {uploaded.name} ({len(file_bytes) / 1024:.0f} KB)")

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("code"):
            with st.expander("Generated code"):
                st.code(msg["code"], language="python")

question = st.chat_input("Ask your question...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if is_tabular:
                    out = answer_question(question, df)

                    if out["success"]:
                        result = out["result"]
                        if isinstance(result, (pd.DataFrame, pd.Series)):
                            st.dataframe(result)
                        else:
                            st.write(result)
                        content = str(result)
                    else:
                        content = (
                            f"The agent could not answer after "
                            f"{out['attempts']} attempts."
                        )
                        st.error(content)

                    with st.expander(f"Generated code (attempts: {out['attempts']})"):
                        st.code(out["code"], language="python")

                    if out["attempts"] > 1:
                        with st.expander("Retry log"):
                            for step in out["log"]:
                                st.write(f"**Attempt {step['attempt']}**")
                                st.code(step["code"], language="python")
                                if step["error"]:
                                    st.error(step["error"])

                    st.session_state.messages.append(
                        {"role": "assistant", "content": content, "code": out["code"]}
                    )
                else:
                    answer = ask_about_file(file_bytes, ext, question)
                    st.markdown(answer)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"Error: {e}"}
                )