import streamlit as st
import yaml

from agent.llm_agent import LLMAgent

st.set_page_config(page_title="Text-to-SQL Agent", page_icon="🔍", layout="wide")


@st.cache_resource
def load_agent() -> LLMAgent:
    return LLMAgent("config.yaml")


def load_config() -> dict:
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def render_sidebar(config: dict):
    with st.sidebar:
        st.title("⚙️ Configuration")
        llm = config["llm"]
        st.markdown(f"**Provider:** `{llm['provider']}`")
        st.markdown(f"**Model:** `{llm['model']}`")
        st.markdown(f"**Max tokens:** `{llm.get('max_tokens', 4096)}`")
        st.divider()
        data = config["data"]
        st.markdown(f"**Excel file:** `{data['excel_file']}`")
        st.markdown(f"**Table name:** `{data['table_name']}`")
        if data.get("sheet_name"):
            st.markdown(f"**Sheet:** `{data['sheet_name']}`")
        st.divider()
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def render_message(msg: dict):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for sql in msg.get("sql_queries", []):
            with st.expander("SQL query"):
                st.code(sql, language="sql")
        for df in msg.get("result_dfs", []):
            st.dataframe(df, use_container_width=True)


def main():
    config = load_config()
    render_sidebar(config)

    st.title("🔍 Text-to-SQL Agent")
    st.caption("Ask questions about your Excel data in plain language.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        render_message(msg)

    user_input = st.chat_input("Ask a question about the data...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    agent = load_agent()
                    history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                        if m["role"] in ("user", "assistant")
                    ]
                    result = agent.chat(user_input, history)
                except Exception as e:
                    result = {"text": f"Error: {e}", "sql_queries": [], "result_dfs": []}

            st.markdown(result["text"])
            for sql in result["sql_queries"]:
                with st.expander("SQL query"):
                    st.code(sql, language="sql")
            for df in result["result_dfs"]:
                st.dataframe(df, use_container_width=True)

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["text"],
            "sql_queries": result["sql_queries"],
            "result_dfs": result["result_dfs"],
        })


if __name__ == "__main__":
    main()
