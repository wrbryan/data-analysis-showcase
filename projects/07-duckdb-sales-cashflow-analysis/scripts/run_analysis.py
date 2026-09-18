from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "sales_cashflow.duckdb"
SQL_DIR = PROJECT_ROOT / "sql"


def run_sql_files() -> None:
    con = duckdb.connect(str(DB_PATH))
    try:
        sql_files = [
            SQL_DIR / "01_create_tables.sql",
            SQL_DIR / "02_sales_performance.sql",
            SQL_DIR / "03_cash_flow.sql",
            SQL_DIR / "04_receivables_aging.sql",
            SQL_DIR / "05_management_summary.sql",
        ]

        for sql_file in sql_files:
            sql_text = sql_file.read_text(encoding="utf-8")
            con.execute(sql_text)
    finally:
        con.close()


def preview_table(table_name: str, limit: int = 10) -> None:
    con = duckdb.connect(str(DB_PATH))
    try:
        df = con.execute(f"SELECT * FROM {table_name} ORDER BY 1 LIMIT {limit}").fetch_df()
        print(f"\n{table_name} preview")
        if df.empty:
            print("No rows returned.")
        else:
            print(df.to_string(index=False))
    finally:
        con.close()


def main() -> None:
    run_sql_files()
    preview_table("management_summary", limit=12)
    preview_table("receivables_aging", limit=10)


if __name__ == "__main__":
    main()
