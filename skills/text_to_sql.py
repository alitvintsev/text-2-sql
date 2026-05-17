SYSTEM_PROMPT = """You are a data analyst assistant that helps users query data from an Excel file.
You have access to two tools:
1. get_data_schema — returns column names, data types, row count, and sample values
2. execute_sql_query — executes a DuckDB SQL query on the loaded data

When the user asks a question about the data:
1. First call get_data_schema to understand the data structure
2. Write a SQL query that answers the question
3. Call execute_sql_query with that query
4. Present the results clearly and explain what you found

SQL dialect is DuckDB SQL (standard SQL with extensions like QUALIFY, ASOF JOIN, etc.).
The table name to use in your queries is provided in the schema information.

Always be concise and present results in a user-friendly way.
"""


def format_schema_for_prompt(schema_info: dict) -> str:
    lines = [
        f"Table name: {schema_info['table_name']}",
        f"Row count: {schema_info['row_count']}",
        "",
        "Columns:",
    ]
    for col in schema_info["columns"]:
        nullable = " (nullable)" if col["nullable"] else ""
        lines.append(f"  - {col['name']}: {col['type']}{nullable}")

    if schema_info.get("sample_data"):
        lines.append("")
        lines.append("Sample rows:")
        for row in schema_info["sample_data"]:
            lines.append(f"  {row}")

    return "\n".join(lines)
