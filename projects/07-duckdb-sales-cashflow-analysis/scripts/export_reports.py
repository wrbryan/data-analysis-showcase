from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "sales_cashflow.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def export_report(query: str, filename: str) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    try:
        df = con.execute(query).fetch_df()
        output_path = OUTPUT_DIR / filename
        df.to_csv(output_path, index=False)
        return len(df)
    finally:
        con.close()


def main() -> None:
    exports = {
        "monthly_financial_summary.csv": "SELECT * FROM management_summary ORDER BY month",
        "product_performance.csv": "SELECT * FROM product_performance ORDER BY gross_profit DESC",
        "cash_flow_summary.csv": "SELECT * FROM monthly_cash_flow ORDER BY month",
        "receivables_aging.csv": "SELECT * FROM receivables_aging ORDER BY days_outstanding DESC",
    }

    for filename, query in exports.items():
        row_count = export_report(query, filename)
        print(f"Created {filename} ({row_count} rows)")


if __name__ == "__main__":
    main()
