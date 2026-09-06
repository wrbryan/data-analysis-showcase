from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import duckdb
import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import Markdown, display


def sanitize_table_name(name: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_]+", "_", name).strip("_")
    if not cleaned:
        return "table"
    if cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    return cleaned


def singularize(name: str) -> str:
    return re.sub(r"s$", "", name)


def list_csv_files(data_dir: Path) -> List[Path]:
    return sorted(path for path in data_dir.glob("*.csv") if path.is_file())


def load_csvs(conn: duckdb.DuckDBPyConnection, data_dir: Path, uploaded_files: Dict[str, Dict] | None = None) -> List[str]:
    data_dir.mkdir(parents=True, exist_ok=True)
    tables: List[str] = []
    if uploaded_files:
        for filename, content in uploaded_files.items():
            if not filename.lower().endswith(".csv"):
                continue
            csv_path = data_dir / filename
            csv_path.write_bytes(content.get("content", b""))
            table_name = sanitize_table_name(Path(filename).stem)
            conn.execute(f"DROP VIEW IF EXISTS {table_name}")
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto(?)", [str(csv_path)])
            tables.append(table_name)
    for csv_path in list_csv_files(data_dir):
        table_name = sanitize_table_name(csv_path.stem)
        conn.execute(f"DROP VIEW IF EXISTS {table_name}")
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto(?)", [str(csv_path)])
        if table_name not in tables:
            tables.append(table_name)
    return tables


def describe_columns(conn: duckdb.DuckDBPyConnection, table_name: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    return [row[1] for row in rows]


def infer_relationships(conn: duckdb.DuckDBPyConnection, tables: List[str]) -> List[Dict[str, str]]:
    proposals: List[Dict[str, str]] = []
    seen = set()

    for index, left_table in enumerate(tables):
        left_cols = describe_columns(conn, left_table)
        for right_table in tables[index + 1 :]:
            right_cols = describe_columns(conn, right_table)
            for left_col in left_cols:
                for right_col in right_cols:
                    if left_col == right_col:
                        candidate = (left_table, left_col, right_table, right_col, "same column name")
                    elif left_col.endswith("_id") and right_col == "id":
                        candidate = (left_table, left_col, right_table, right_col, "child key to primary key")
                    elif left_col == "id" and right_col.endswith("_id"):
                        candidate = (left_table, left_col, right_table, right_col, "primary key to child key")
                    elif left_col == f"{singularize(right_table)}_id" and right_col == "id":
                        candidate = (left_table, left_col, right_table, right_col, "table-name-based key match")
                    elif right_col == f"{singularize(left_table)}_id" and left_col == "id":
                        candidate = (left_table, left_col, right_table, right_col, "table-name-based key match")
                    else:
                        continue

                    key = (candidate[0], candidate[1], candidate[2], candidate[3])
                    if key not in seen:
                        seen.add(key)
                        proposals.append(
                            {
                                "source_table": left_table,
                                "source_column": left_col,
                                "target_table": right_table,
                                "target_column": right_col,
                                "reason": candidate[4],
                            }
                        )
    return proposals


def approve_relationships(conn: duckdb.DuckDBPyConnection, proposals: List[Dict[str, str]]) -> List[str]:
    created: List[str] = []
    for proposal in proposals:
        view_name = sanitize_table_name(f"view_{proposal['source_table']}_{proposal['target_table']}")
        sql = (
            f"CREATE OR REPLACE VIEW {view_name} AS "
            f"SELECT a.*, b.* FROM {proposal['source_table']} AS a "
            f"JOIN {proposal['target_table']} AS b "
            f"ON a.{proposal['source_column']} = b.{proposal['target_column']}"
        )
        conn.execute(sql)
        created.append(view_name)
    return created


def preview_table(conn: duckdb.DuckDBPyConnection, table_name: str, limit: int = 10) -> pd.DataFrame:
    return conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}").fetchdf()


def run_query(conn: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return conn.execute(sql).fetchdf()


def get_schema(conn: duckdb.DuckDBPyConnection, table_name: str) -> List[tuple]:
    return conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()


def insert_row(conn: duckdb.DuckDBPyConnection, table_name: str, values: List[str]) -> None:
    cols = [row[1] for row in get_schema(conn, table_name)]
    placeholders = ", ".join(["?"] * len(cols))
    col_sql = ", ".join([f'"{c}"' for c in cols])
    conn.execute(f"INSERT INTO {table_name} ({col_sql}) VALUES ({placeholders})", values)


def delete_row(conn: duckdb.DuckDBPyConnection, table_name: str, pk_value: str) -> None:
    pk_col = [row[1] for row in get_schema(conn, table_name) if row[5] == 1][0]
    conn.execute(f'DELETE FROM {table_name} WHERE "{pk_col}" = ?', [pk_value])


def export_to_sheet(df: pd.DataFrame, sheet_name: str = "DuckDB_Report") -> str:
    import gspread

    try:
        from google.colab import auth

        auth.authenticate_user()
    except Exception:
        pass

    try:
        from google.auth import default

        creds, _ = default()
        gc = gspread.authorize(creds)
    except Exception as exc:  # pragma: no cover - optional runtime path
        raise RuntimeError("Google Sheets export needs Colab auth or service-account credentials.") from exc

    sh = gc.create(sheet_name)
    worksheet = sh.sheet1
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    return sh.url


def make_chart(df: pd.DataFrame, chart_type: str = "bar") -> None:
    if df.empty:
        raise ValueError("No data to chart.")
    if len(df.columns) < 2:
        raise ValueError("Need at least two columns for a chart.")
    x_col = df.columns[0]
    y_col = df.columns[1]
    fig, ax = plt.subplots(figsize=(6, 4))
    if chart_type == "bar":
        ax.bar(df[x_col].astype(str), df[y_col])
    elif chart_type == "line":
        ax.plot(df[x_col].astype(str), df[y_col], marker="o")
    else:
        ax.scatter(df[x_col].astype(str), df[y_col])
    ax.set_title("Chart from query result")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.tick_params(axis="x", rotation=30)
    plt.tight_layout()
    plt.show()


def build_gui(project_dir: Path | None = None) -> widgets.VBox:
    project_dir = Path(project_dir or Path.cwd())
    data_dir = project_dir / "data"
    db_path = project_dir / "duckdb_gui.duckdb"
    conn = duckdb.connect(str(db_path))
    output = widgets.Output(layout=widgets.Layout(border="1px solid #d0d7de", padding="12px", width="100%"))
    status = widgets.HTML("<b>Status:</b> No data loaded yet.")
    relation_container = widgets.VBox([])
    checkbox_items: List[widgets.Checkbox] = []
    upload_widget = widgets.FileUpload(accept=".csv", multiple=True)
    query_input = widgets.Textarea(value="SELECT * FROM table_name LIMIT 10;", layout=widgets.Layout(width="100%", height="100px"))
    table_select = widgets.Dropdown(options=[], description="Table:", layout=widgets.Layout(width="220px"))
    chart_type = widgets.Dropdown(options=["bar", "line", "scatter"], value="bar", description="Chart:")

    def refresh_relationships(_event=None) -> None:
        nonlocal checkbox_items
        with output:
            output.clear_output()
            uploaded_files = upload_widget.value or {}
            tables = load_csvs(conn, data_dir, uploaded_files=uploaded_files or None)
            table_select.options = tables
            if tables and table_select.value not in tables:
                table_select.value = tables[0]
            proposals = infer_relationships(conn, tables)
            checkbox_items = []
            if not proposals:
                relation_container.children = [widgets.HTML("No obvious relationships were detected. You can still query the tables directly.")]
                status.value = f"<b>Status:</b> Loaded {len(tables)} table(s)."
                return

            rows = []
            for proposal in proposals:
                checkbox = widgets.Checkbox(value=True, description=f"{proposal['source_table']}.{proposal['source_column']} -> {proposal['target_table']}.{proposal['target_column']}")
                checkbox.proposal = proposal
                rows.append(widgets.HBox([checkbox, widgets.Label(proposal["reason"])]))
                checkbox_items.append(checkbox)
            relation_container.children = rows
            status.value = f"<b>Status:</b> Loaded {len(tables)} table(s) and inferred relationships."

    def approve_selected(_event=None) -> None:
        with output:
            output.clear_output()
            selected = [checkbox.proposal for checkbox in checkbox_items if getattr(checkbox, "value", False)]
            if not selected:
                print("No relationships selected.")
                return
            created_views = approve_relationships(conn, selected)
            print(f"Approved {len(selected)} relationship(s). Views created: {', '.join(created_views)}")

    def show_table(_event=None) -> None:
        with output:
            output.clear_output()
            if not table_select.value:
                print("Select a table first.")
                return
            display(Markdown(f"### {table_select.value}"))
            display(preview_table(conn, table_select.value))
            display(Markdown("#### Schema"))
            display(pd.DataFrame(get_schema(conn, table_select.value), columns=["cid", "name", "type", "notnull", "dflt_value", "pk"]))

    def run_sql(_event=None) -> None:
        with output:
            output.clear_output()
            try:
                result = run_query(conn, query_input.value)
                display(result)
            except Exception as exc:  # pragma: no cover - runtime path
                print(f"Error: {exc}")

    def run_sql_and_export(_event=None) -> None:
        with output:
            output.clear_output()
            try:
                result = run_query(conn, query_input.value)
                display(result)
                sheet_url = export_to_sheet(result, sheet_name="DuckDB_Report")
                print(f"Exported to Google Sheets: {sheet_url}")
            except Exception as exc:  # pragma: no cover - runtime path
                print(f"Error: {exc}")

    def run_sql_and_chart(_event=None) -> None:
        with output:
            output.clear_output()
            try:
                result = run_query(conn, query_input.value)
                display(result)
                make_chart(result, chart_type=chart_type.value)
            except Exception as exc:  # pragma: no cover - runtime path
                print(f"Error: {exc}")

    def add_row(_event=None) -> None:
        with output:
            output.clear_output()
            if not table_select.value:
                print("Select a table first.")
                return
            schema = get_schema(conn, table_select.value)
            cols = [row[1] for row in schema]
            print("Enter values separated by commas:")
            print(", ".join(cols))
            values = input().split(",")
            insert_row(conn, table_select.value, [v.strip() for v in values])
            print("Row inserted successfully.")

    def remove_row(_event=None) -> None:
        with output:
            output.clear_output()
            if not table_select.value:
                print("Select a table first.")
                return
            pk_value = input("Enter the primary key value to delete: ")
            delete_row(conn, table_select.value, pk_value)
            print("Row deleted successfully.")

    load_button = widgets.Button(description="Load Uploaded CSVs", button_style="primary")
    approve_button = widgets.Button(description="Approve Selected", button_style="success")
    show_button = widgets.Button(description="Show Table")
    query_button = widgets.Button(description="Run SQL")
    export_button = widgets.Button(description="Run SQL + Export")
    chart_button = widgets.Button(description="Run SQL + Chart")
    insert_button = widgets.Button(description="Insert Row")
    delete_button = widgets.Button(description="Delete Row")

    load_button.on_click(refresh_relationships)
    approve_button.on_click(approve_selected)
    show_button.on_click(show_table)
    query_button.on_click(run_sql)
    export_button.on_click(run_sql_and_export)
    chart_button.on_click(run_sql_and_chart)
    insert_button.on_click(add_row)
    delete_button.on_click(remove_row)

    refresh_relationships(None)

    return widgets.VBox(
        [
            widgets.HTML('<div style="font-size: 18px; font-weight: 600; color: #1f2937;">DuckDB CSV Relationship Manager</div>'),
            widgets.HTML("Upload CSV files, inspect tables, run SQL, approve relationships, and visualize results in a polished workflow."),
            widgets.HTML("<b>1. Upload CSV files</b>"),
            upload_widget,
            widgets.HBox([load_button, approve_button]),
            widgets.HTML("<b>2. Inspect and query</b>"),
            widgets.HBox([table_select, show_button, insert_button, delete_button]),
            query_input,
            widgets.HBox([query_button, export_button, chart_button, chart_type]),
            status,
            relation_container,
            output,
        ],
        layout=widgets.Layout(width="100%"),
    )
