# DuckDB CSV Notebook GUI

Turn messy CSV files into a lightweight analytics workflow in minutes.

![Project banner](docs/banner.svg)

A polished notebook-based workflow for turning uploaded CSV files into a lightweight DuckDB database, inferring likely relationships, approving them interactively, and exploring the data with SQL, charts, and Google Sheets export.

This project is designed as a boss-friendly demo for showing how raw spreadsheets can become a usable analytics workflow without writing a full application backend.

## About

This repository provides a notebook-driven prototype for turning CSV files into a lightweight relational analytics workflow using DuckDB. It is built for demos, rapid prototyping, and showing how raw data can be cleaned, connected, queried, visualized, and shared without a full database stack.

## Highlights

- Upload CSV files and load them into DuckDB tables
- Infer likely table relationships and approve them interactively
- Inspect tables and schemas directly in the notebook
- Run SQL queries and review results inline
- Export query results to Google Sheets
- Create simple bar, line, or scatter charts from query output

## Quick start

1. Create and activate a Python environment.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch Jupyter:
   ```bash
   jupyter notebook
   ```
4. Open the notebook named `duckdb_csv_gui.ipynb`.

For Google Colab, use `duckdb_csv_gui_colab.ipynb`.

## Project structure

- `duckdb_csv_gui.py`: core logic for loading CSVs, inferring relationships, and building the GUI.

![Notebook preview](docs/notebook-preview.svg)
- `duckdb_csv_gui.ipynb`: local notebook UI for the workflow.
- `duckdb_csv_gui_colab.ipynb`: Colab-compatible version with the same workflow.
- `data/`: sample CSV files that demonstrate the workflow.
- `tests/`: regression tests for the core workflow.

## Demo idea

Use this project to show how a business user can:
- import messy CSV files,
- instantly create a lightweight relational data model,
- run exploratory SQL,
- and generate a report-ready view for a presentation.
