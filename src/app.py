import pandas as pd
import streamlit as st

from run_query import get_code, clean_code, run_code

st.set_page_config(page_title="InsightAgent", page_icon="📊", layout="wide")
st.title("📊 InsightAgent")
st.caption("Upload your dataset and ask question in English.")


def load_data(file):
    if file.name.lower().endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


# Sidebar: dataset upload
with st.sidebar:
    st.header("Dataset")
    uploaded = st.file_uploader("Choose Either CSV or Excel File", type=["csv", "xlsx"])

if uploaded is None:
    st.info("To start upload the csv file on the right side column.")
    st.stop()

# Naya file aaye to chat history reset karein
if st.session_state.get("file_name") != uploaded.name:
    st.session_state.file_name = uploaded.name
    st.session_state.messages = []

df = load_data(uploaded)

with st.sidebar:
    st.success(f"{df.shape[0]} rows, {df.shape[1]} columns")
    st.write("**Columns:**", list(df.columns))

with st.expander("Dataset preview (First 5 rows)"):
    st.dataframe(df.head())

# Purani chat dikhayein
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("code"):
            with st.expander("Generated code"):
                st.code(msg["code"], language="python")

# Naya sawaal
question = st.chat_input("Any question? ...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking on basis of the dataset..."):
            try:
                code = clean_code(get_code(question, list(df.columns)))
                result = run_code(code, df)

                if isinstance(result, (pd.DataFrame, pd.Series)):
                    st.dataframe(result)
                else:
                    st.write(result)

                with st.expander("Generated code"):
                    st.code(code, language="python")

                st.session_state.messages.append(
                    {"role": "assistant", "content": str(result), "code": code}
                )
            except Exception as e:
                st.error(f"Error aaya: {e}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"Error: {e}"}
                )