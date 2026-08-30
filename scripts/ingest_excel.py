"""Simple Excel ingestion helper.
Reads all sheets from an Excel workbook and writes cleaned CSVs to data/
"""
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCEL_DIR = ROOT / "excel"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def ingest_workbook(path: pathlib.Path):
    xls = pd.ExcelFile(path)
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        # basic cleanup: drop fully empty rows/cols
        df.dropna(axis=0, how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        out_path = DATA_DIR / f"{path.stem}--{sheet}.csv"
        df.to_csv(out_path, index=False)
        print(f"Wrote {out_path}")


if __name__ == '__main__':
    for f in EXCEL_DIR.glob("*.xlsx"):
        ingest_workbook(f)
    print("Done")