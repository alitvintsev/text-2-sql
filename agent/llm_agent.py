import json
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml
from dotenv import load_dotenv

from skills.pandas_query import execute_query, format_query_result, get_schema, load_excel_data
from skills.text_to_sql import SYSTEM_PROMPT, format_schema_for_prompt

load_dotenv()


class LLMAgent:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        data_cfg = self.config["data"]
        self.df = load_excel_data(data_cfg["excel_file"], data_cfg.get("sheet_name"))
        self.table_name = data_cfg["table_name"]

        self.provider = self.config["llm"]["provider"]
        self.model = self.config["llm"]["model"]
        self.max_tokens = self.config["llm"].get("max_tokens", 4096)

        api_key = os.environ.get(self.config["llm"]["api_key_env"], "")
        self.client = self._init_client(api_key)

    def _init_client(self, api_key: str):
        if self.provider == "anthropic":
            import anthropic
            return anthropic.Anthropic(api_key=api_key)
        elif self.provider == "openai":
            import openai
            return openai.OpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _get_tools_anthropic(self) -> list:
        return [
            {
                "name": "get_data_schema",
                "description": "Returns the schema of the loaded Excel data: column names, types, row count, and sample rows.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "execute_sql_query",
                "description": "Executes a DuckDB SQL query against the loaded Excel data and returns the results.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "The SQL query to execute. Use the table name from the schema.",
                        }
                    },
                    "required": ["sql"],
                },
            },
        ]

    def _get_tools_openai(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_data_schema",
                    "description": "Returns the schema of the loaded Excel data: column names, types, row count, and sample rows.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_sql_query",
                    "description": "Executes a DuckDB SQL query against the loaded Excel data and returns the results.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "The SQL query to execute. Use the table name from the schema.",
                            }
                        },
                        "required": ["sql"],
                    },
                },
            },
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> tuple[str, Optional[pd.DataFrame], Optional[str]]:
        if tool_name == "get_data_schema":
            schema = get_schema(self.df, self.table_name)
            return format_schema_for_prompt(schema), None, None

        if tool_name == "execute_sql_query":
            sql = tool_input["sql"]
            result = execute_query(self.df, sql, self.table_name)
            text = format_query_result(result)
            df_result = result["data"] if result["success"] else None
            return text, df_result, sql

        return f"Unknown tool: {tool_name}", None, None

    def chat(self, user_message: str, chat_history: list = None) -> dict:
        if self.provider == "anthropic":
            return self._chat_anthropic(user_message, chat_history or [])
        elif self.provider == "openai":
            return self._chat_openai(user_message, chat_history or [])
        raise ValueError(f"Unknown provider: {self.provider}")

    def _chat_anthropic(self, user_message: str, chat_history: list) -> dict:
        messages = [{"role": m["role"], "content": m["content"]} for m in chat_history]
        messages.append({"role": "user", "content": user_message})

        tools = self._get_tools_anthropic()
        sql_queries: list[str] = []
        result_dfs: list[pd.DataFrame] = []
        final_text = ""

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result_text, result_df, sql = self._execute_tool(block.name, block.input)
                        if sql:
                            sql_queries.append(sql)
                        if result_df is not None:
                            result_dfs.append(result_df)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        })
                messages.append({"role": "user", "content": tool_results})

            else:
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text
                break

        return {"text": final_text, "sql_queries": sql_queries, "result_dfs": result_dfs}

    def _chat_openai(self, user_message: str, chat_history: list) -> dict:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [{"role": m["role"], "content": m["content"]} for m in chat_history]
        messages.append({"role": "user", "content": user_message})

        tools = self._get_tools_openai()
        sql_queries: list[str] = []
        result_dfs: list[pd.DataFrame] = []
        final_text = ""

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=tools,
                messages=messages,
            )

            choice = response.choices[0]
            messages.append(choice.message)

            if choice.finish_reason == "tool_calls":
                for tool_call in choice.message.tool_calls:
                    tool_input = json.loads(tool_call.function.arguments)
                    result_text, result_df, sql = self._execute_tool(tool_call.function.name, tool_input)
                    if sql:
                        sql_queries.append(sql)
                    if result_df is not None:
                        result_dfs.append(result_df)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text,
                    })
            else:
                final_text = choice.message.content or ""
                break

        return {"text": final_text, "sql_queries": sql_queries, "result_dfs": result_dfs}
