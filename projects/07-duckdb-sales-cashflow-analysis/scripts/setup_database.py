from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "sales_cashflow.duckdb"
SQL_DIR = PROJECT_ROOT / "sql"


def build_database() -> None:
    con = duckdb.connect(str(DB_PATH))
    try:
        create_sql = (SQL_DIR / "01_create_tables.sql").read_text(encoding="utf-8")
        con.execute(create_sql)
    finally:
        con.close()


def print_summary() -> None:
    con = duckdb.connect(str(DB_PATH))
    try:
        summary = con.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM sales_orders) AS sales_order_count,
                (SELECT COUNT(*) FROM cash_receipts) AS receipt_count,
                (SELECT COUNT(*) FROM operating_expenses) AS expense_count,
                (SELECT ROUND(COALESCE(SUM(revenue), 0), 2) FROM sales_orders) AS total_revenue,
                (SELECT ROUND(COALESCE(SUM(cash_received), 0), 2) FROM cash_receipts) AS total_cash_received;
            """
        ).fetchone()

        sales_order_count, receipt_count, expense_count, total_revenue, total_cash_received = summary
        print(f"Sales orders: {sales_order_count}")
        print(f"Cash receipts: {receipt_count}")
        print(f"Operating expenses: {expense_count}")
        print(f"Total revenue: ${total_revenue:,.2f}")
        print(f"Total cash received: ${total_cash_received:,.2f}")
    finally:
        con.close()


def main() -> None:
    build_database()
    print_summary()


if __name__ == "__main__":
    main()
