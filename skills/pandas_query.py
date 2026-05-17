import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional


def load_excel_data(file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    df = pd.read_excel(path, sheet_name=sheet_name or 0)
    return df


def get_schema(df: pd.DataFrame, table_name: str) -> dict:
    columns = []
    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            col_type = "INTEGER"
        elif pd.api.types.is_float_dtype(dtype):
            col_type = "FLOAT"
        elif pd.api.types.is_bool_dtype(dtype):
            col_type = "BOOLEAN"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            col_type = "TIMESTAMP"
        else:
            col_type = "VARCHAR"

        columns.append({
            "name": col,
            "type": col_type,
            "nullable": bool(df[col].isna().any()),
        })

    sample_rows = df.head(3).to_dict(orient="records")

    return {
        "table_name": table_name,
        "row_count": len(df),
        "columns": columns,
        "sample_data": sample_rows,
    }


def execute_query(df: pd.DataFrame, sql: str, table_name: str) -> dict:
    try:
        conn = duckdb.connect()
        conn.register(table_name, df)
        result_df = conn.execute(sql).fetchdf()
        conn.close()
        return {
            "success": True,
            "data": result_df,
            "row_count": len(result_df),
            "columns": list(result_df.columns),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None,
            "row_count": 0,
            "columns": [],
        }


def format_query_result(result: dict) -> str:
    if not result["success"]:
        return f"Query error: {result['error']}"

    if result["row_count"] == 0:
        return "Query returned no rows."

    df = result["data"]
    lines = [f"Result: {result['row_count']} row(s), columns: {', '.join(result['columns'])}"]

    if result["row_count"] <= 20:
        lines.append(df.to_string(index=False))
    else:
        lines.append(df.head(20).to_string(index=False))
        lines.append(f"... ({result['row_count'] - 20} more rows)")

    return "\n".join(lines)
