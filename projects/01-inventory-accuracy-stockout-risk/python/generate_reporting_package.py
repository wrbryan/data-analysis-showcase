"""Generate the two-page Inventory Accuracy & Stockout Risk reporting package from published outputs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
REPORTING_DIR = PROJECT_ROOT / "reporting"

EXPECTED_ROWS = {
    "kpi_summary.csv": 31,
    "sku_replenishment_priorities.csv": 300,
    "sku_location_count_priorities.csv": 3600,
    "location_variance_summary.csv": 12,
    "stockout_risk_report.csv": 8,
    "data_quality_checks.csv": 26,
}

REQUIRED_COLUMNS = {
    "kpi_summary.csv": {
        "metric_name", "metric_value", "metric_unit", "calculation_note"
    },
    "sku_replenishment_priorities.csv": {
        "priority_rank", "sku", "product_name", "supplier",
        "total_physical_qty", "days_of_supply", "replenishment_tier",
    },
    "sku_location_count_priorities.csv": {
        "priority_rank", "sku", "location", "control_tier",
        "recommended_count_frequency", "location_adjustment_exposure",
        "variance_event_count", "recount_rate", "priority_score",
    },
    "location_variance_summary.csv": {
        "location", "total_adjustment_value", "recurring_variance_pairs",
        "recount_count",
    },
    "stockout_risk_report.csv": {
        "priority_rank", "sku", "product_name", "supplier",
        "total_physical_qty", "days_of_supply", "replenishment_tier",
        "recommended_action",
    },
    "data_quality_checks.csv": {
        "check_name", "status", "records_affected", "details"
    },
}

COLORS = {
    "navy": "#17324D",
    "ink": "#1F2933",
    "muted": "#52606D",
    "line": "#CBD5E1",
    "paper": "#F4F7FA",
    "white": "#FFFFFF",
    "red": "#C94C4C",
    "orange": "#E76F51",
    "amber": "#F4A261",
    "teal": "#2A9D8F",
    "green": "#1B5E20",
    "green_fill": "#E8F5E9",
    "callout": "#FFF7ED",
    "blue_fill": "#E7F0F7",
}


def load_outputs() -> dict[str, pd.DataFrame]:
    frames = {}
    for filename, required in REQUIRED_COLUMNS.items():
        path = OUTPUT_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing published output: {path}")
        frame = pd.read_csv(path)
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{filename} is missing columns: {sorted(missing)}")
        expected = EXPECTED_ROWS[filename]
        if len(frame) != expected:
            raise ValueError(
                f"{filename} has {len(frame)} rows; expected {expected}"
            )
        frames[filename] = frame

    quality = frames["data_quality_checks.csv"]
    if not quality["status"].eq("PASS").all():
        failed = quality.loc[quality["status"] != "PASS", "check_name"].tolist()
        raise ValueError(f"Data-quality checks failed: {failed}")
    return frames


def metric(kpi: pd.DataFrame, name: str) -> float:
    matches = kpi.loc[kpi["metric_name"] == name, "metric_value"]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one KPI row for {name}")
    return float(matches.iloc[0])


def configure_page(fig: plt.Figure, title: str, subtitle: str = "") -> None:
    fig.patch.set_facecolor(COLORS["paper"])
    fig.text(0.035, 0.965, title, fontsize=22, weight="bold",
             color=COLORS["navy"], va="top")
    if subtitle:
        fig.text(0.035, 0.935, subtitle, fontsize=10.5,
                 color=COLORS["muted"], va="top")


def style_axis(axis: plt.Axes) -> None:
    axis.set_facecolor(COLORS["white"])
    for spine in axis.spines.values():
        spine.set_edgecolor(COLORS["line"])
    axis.tick_params(labelsize=8, colors=COLORS["ink"])
    axis.grid(axis="y", alpha=0.18)
    axis.set_axisbelow(True)


def add_card(axis: plt.Axes, label: str, value: str, color: str) -> None:
    axis.set_facecolor(COLORS["white"])
    axis.set_xticks([])
    axis.set_yticks([])
    for spine in axis.spines.values():
        spine.set_edgecolor(COLORS["line"])
    axis.text(0.5, 0.68, label, ha="center", va="center", fontsize=8.2,
              color=COLORS["muted"], weight="bold", wrap=True)
    axis.text(0.5, 0.25, value, ha="center", va="center", fontsize=17,
              color=color, weight="bold")


def add_table(axis: plt.Axes, frame: pd.DataFrame, columns: list[str],
              widths: list[float], font_size: float = 7.4,
              header_color: str = COLORS["navy"]) -> None:
    axis.axis("off")
    table = axis.table(
        cellText=frame[columns].values,
        colLabels=columns,
        colWidths=widths,
        cellLoc="left",
        colLoc="left",
        bbox=[0, 0, 1, 1],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    for (row, column), cell in table.get_celld().items():
        cell.set_edgecolor(COLORS["line"])
        cell.PAD = 0.025
        if row == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color=COLORS["white"], weight="bold")
        else:
            cell.set_facecolor(COLORS["white"] if row % 2 else "#F8FAFC")
            cell.set_text_props(color=COLORS["ink"])
    return table


def build_page_one(frames: dict[str, pd.DataFrame]) -> plt.Figure:
    kpi = frames["kpi_summary.csv"]
    replenishment = frames["sku_replenishment_priorities.csv"]
    count_priority = frames["sku_location_count_priorities.csv"]
    locations = frames["location_variance_summary.csv"]

    fig = plt.figure(figsize=(16, 9), facecolor=COLORS["paper"])
    grid = fig.add_gridspec(
        14, 24, left=0.035, right=0.965, top=0.89, bottom=0.08,
        hspace=1.0, wspace=0.8,
    )
    configure_page(
        fig,
        "Inventory Accuracy & Stockout Risk | Executive Control Tower",
        "Validated Inventory Accuracy & Stockout Risk outputs | two decision grains kept intentionally separate",
    )
    fig.text(
        0.965, 0.957, "Data Quality: 26 / 26 Checks Passed", ha="right",
        va="top", fontsize=9.5, weight="bold", color=COLORS["green"],
        bbox={"boxstyle": "round,pad=0.35", "facecolor": COLORS["green_fill"],
              "edgecolor": "#A5D6A7"},
    )

    cards = [
        ("Critical + High\nReplenishment SKUs", "8", COLORS["navy"]),
        ("Critical + High\nReplenishment Rate", "2.67%", COLORS["navy"]),
        ("Weekly Cycle-Count\nAssignments", "6", COLORS["navy"]),
        ("Biweekly Cycle-Count\nAssignments", "472", COLORS["navy"]),
        ("Inventory Record\nAccuracy", "100.00%", COLORS["navy"]),
        ("Cumulative Adjustment\nExposure", "$211,618.40", COLORS["red"]),
        ("Cycle-Count\nCompletion", "94.12%", COLORS["navy"]),
        ("Recount Rate", "14.10%", COLORS["navy"]),
        ("On-Time Shipment\nRate", "90.90%", COLORS["navy"]),
    ]
    for index, card in enumerate(cards):
        row = (index // 3) * 2
        column = (index % 3) * 8
        add_card(fig.add_subplot(grid[row:row + 2, column:column + 6]), *card)

    action_axis = fig.add_subplot(grid[6:10, 16:24])
    action_axis.set_facecolor(COLORS["callout"])
    action_axis.set_xticks([])
    action_axis.set_yticks([])
    for spine in action_axis.spines.values():
        spine.set_edgecolor(COLORS["amber"])
    action_axis.text(
        0.03, 0.95,
        "ACTION NOW\n\n"
        "1. Review the 8 Critical + High SKUs for\n"
        "total supply position, inbound status,\n"
        "and replenishment-policy settings.\n\n"
        "2. Execute the 6 weekly and 472 biweekly\n"
        "SKU/location cycle-count assignments.\n\n"
        "3. Investigate locations with recurring\n"
        "variance and adjustment exposure.\n\n"
        "Decision grains:\n"
        "Replenishment risk = SKU across all locations.\n"
        "Count-control risk = SKU/location.",
        va="top", fontsize=7.2, color=COLORS["ink"], linespacing=1.05,
    )

    tier_order = ["Critical", "High", "Watch", "Routine"]
    tier_counts = replenishment["replenishment_tier"].value_counts().reindex(tier_order)
    axis = fig.add_subplot(grid[10:14, 0:8])
    style_axis(axis)
    axis.bar(tier_order, tier_counts.values,
             color=[COLORS["red"], COLORS["orange"], COLORS["amber"], "#A8DADC"])
    axis.set_title("Current SKU Replenishment Risk", loc="left", fontsize=10.5,
                   weight="bold", color=COLORS["navy"])
    axis.set_ylabel("SKU records", fontsize=8)
    for index, value in enumerate(tier_counts.values):
        axis.text(index, value + 4, f"{value:,}", ha="center", fontsize=8)
    axis.text(0, -0.23, "Replenishment risk = SKU across all locations",
              transform=axis.transAxes, fontsize=7.5, color=COLORS["muted"])

    frequency_order = ["Weekly", "Biweekly", "Monthly", "Quarterly"]
    frequency_counts = count_priority["recommended_count_frequency"].value_counts().reindex(frequency_order)
    axis = fig.add_subplot(grid[10:14, 8:16])
    axis.set_facecolor(COLORS["white"])
    for spine in axis.spines.values():
        spine.set_edgecolor(COLORS["line"])
    axis.barh(frequency_order, frequency_counts.values, color=COLORS["teal"])
    axis.set_title("Recommended Cycle-Count Workload", loc="left", fontsize=10.5,
                   weight="bold", color=COLORS["navy"])
    axis.set_xlabel("SKU/location assignments", fontsize=8)
    axis.tick_params(labelsize=8)
    axis.grid(axis="x", alpha=0.18)
    axis.set_axisbelow(True)
    for index, value in enumerate(frequency_counts.values):
        axis.text(value + 35, index, f"{value:,}", va="center", fontsize=8)
    axis.text(0, -0.23, "Count-control risk = SKU/location",
              transform=axis.transAxes, fontsize=7.5, color=COLORS["muted"])

    positive_locations = locations.loc[locations["total_adjustment_value"] > 0].sort_values(
        "total_adjustment_value", ascending=False
    )
    axis = fig.add_subplot(grid[10:14, 16:24])
    axis.set_facecolor(COLORS["white"])
    for spine in axis.spines.values():
        spine.set_edgecolor(COLORS["line"])
    axis.barh(positive_locations["location"], positive_locations["total_adjustment_value"],
              color=COLORS["orange"])
    axis.invert_yaxis()
    axis.set_title("Locations With Highest Adjustment Exposure", loc="left",
                   fontsize=10.5, weight="bold", color=COLORS["navy"])
    axis.set_xlabel("Adjustment exposure ($)", fontsize=8)
    axis.tick_params(labelsize=8)
    axis.grid(axis="x", alpha=0.18)
    axis.set_axisbelow(True)
    for index, value in enumerate(positive_locations["total_adjustment_value"]):
        axis.text(value + 1500, index, f"${value:,.2f}", va="center", fontsize=8)
    axis.text(0, -0.23, "Location-level exposure | nonzero locations only",
              transform=axis.transAxes, fontsize=7.5, color=COLORS["muted"])

    fig.text(
        0.035, 0.025,
        "Deterministic synthetic data for portfolio demonstration; no employer or client data is included.",
        fontsize=8, color=COLORS["muted"],
    )
    return fig


def build_page_two(frames: dict[str, pd.DataFrame]) -> plt.Figure:
    stockout = frames["stockout_risk_report.csv"].sort_values("priority_rank")
    count_priority = frames["sku_location_count_priorities.csv"].sort_values(
        ["priority_score", "priority_rank"], ascending=[False, True]
    ).head(15)
    locations = frames["location_variance_summary.csv"].loc[
        frames["location_variance_summary.csv"]["total_adjustment_value"] > 0
    ].sort_values("total_adjustment_value", ascending=False)

    fig = plt.figure(figsize=(16, 9), facecolor=COLORS["paper"])
    grid = fig.add_gridspec(
        24, 24, left=0.035, right=0.965, top=0.91, bottom=0.06,
        hspace=1.15, wspace=0.8,
    )
    configure_page(
        fig,
        "Action Queues and Evidence",
        "Published output evidence | ranked queues and accountable operating response",
    )

    fig.text(0.035, 0.875, "Critical/High Replenishment Queue | 8 records",
             fontsize=10.5, weight="bold", color=COLORS["navy"])
    stockout_display = stockout.assign(
        Priority=stockout["priority_rank"].astype(int),
        SKU=stockout["sku"],
        Product=stockout["product_name"],
        Supplier=stockout["supplier"],
        **{
            "On Hand": stockout["total_physical_qty"].map(lambda value: f"{value:,.0f}"),
            "Days of Supply": stockout["days_of_supply"].map(lambda value: f"{value:,.2f}"),
            "Tier": stockout["replenishment_tier"],
            "Recommended Action": stockout["recommended_action"],
        },
    )
    axis = fig.add_subplot(grid[1:7, 0:24])
    add_table(
        axis, stockout_display,
        ["Priority", "SKU", "Product", "Supplier", "On Hand", "Days of Supply", "Tier", "Recommended Action"],
        [0.06, 0.08, 0.17, 0.14, 0.08, 0.10, 0.08, 0.29],
        font_size=7.1,
    )

    fig.text(0.035, 0.625, "Count-Priority Evidence | top 15 by priority score",
             fontsize=10.5, weight="bold", color=COLORS["navy"])
    count_display = count_priority.assign(
        Priority=count_priority["priority_rank"].astype(int),
        SKU=count_priority["sku"],
        Location=count_priority["location"],
        Tier=count_priority["control_tier"],
        Frequency=count_priority["recommended_count_frequency"],
        **{
            "Adjustment Exposure": count_priority["location_adjustment_exposure"].map(
                lambda value: f"${value:,.2f}"
            ),
            "Variance Events": count_priority["variance_event_count"].astype(int),
            "Recount Rate": count_priority["recount_rate"].map(lambda value: f"{value:,.2f}%"),
        },
    )
    axis = fig.add_subplot(grid[9:16, 0:24])
    add_table(
        axis, count_display,
        ["Priority", "SKU", "Location", "Tier", "Frequency", "Adjustment Exposure", "Variance Events", "Recount Rate"],
        [0.08, 0.10, 0.12, 0.10, 0.12, 0.18, 0.14, 0.14],
        font_size=7.2,
        header_color=COLORS["teal"],
    )

    fig.text(0.035, 0.345, "Nonzero Location Exposure | 2 locations",
             fontsize=10.5, weight="bold", color=COLORS["navy"])
    location_display = locations.assign(
        Location=locations["location"],
        **{
            "Adjustment Exposure": locations["total_adjustment_value"].map(
                lambda value: f"${value:,.2f}"
            ),
            "Recurring Variance Pairs": locations["recurring_variance_pairs"].astype(int),
            "Recount Count": locations["recount_count"].astype(int),
        },
    )
    axis = fig.add_subplot(grid[18:21, 0:13])
    add_table(
        axis, location_display,
        ["Location", "Adjustment Exposure", "Recurring Variance Pairs", "Recount Count"],
        [0.20, 0.30, 0.30, 0.20],
        font_size=8,
        header_color=COLORS["orange"],
    )

    axis = fig.add_subplot(grid[18:24, 14:24])
    axis.axis("off")
    axis.add_patch(FancyBboxPatch(
        (0, 0), 1, 1, boxstyle="round,pad=0.012", linewidth=1,
        edgecolor=COLORS["line"], facecolor=COLORS["white"],
        transform=axis.transAxes,
    ))
    matrix = (
        "ACTION AND OWNER MATRIX\n\n"
        "Replenishment review\n"
        "Inventory Control Lead / Replenishment Planner\n\n"
        "Weekly and biweekly count execution\n"
        "Cycle Count Team Lead\n\n"
        "Location-control investigation\n"
        "Warehouse Operations Manager\n\n"
        "Data-quality validation before refresh\n"
        "Data/Systems Analyst"
    )
    axis.text(0.04, 0.94, matrix, va="top", fontsize=7.5,
              color=COLORS["ink"], linespacing=1.05)

    fig.text(0.035, 0.025,
             "26 / 26 data-quality checks passed. Source data is deterministic synthetic portfolio data.",
             fontsize=8, color=COLORS["muted"])
    return fig


def generate_package(output_dir: Path = REPORTING_DIR) -> None:
    frames = load_outputs()
    output_dir.mkdir(parents=True, exist_ok=True)
    page_one = build_page_one(frames)
    page_two = build_page_two(frames)

    page_one_path = output_dir / "01-executive-control-tower.png"
    page_two_path = output_dir / "02-action-queues-and-evidence.png"
    pdf_path = output_dir / "inventory-accuracy-stockout-risk-report.pdf"
    page_one.savefig(page_one_path, dpi=180, facecolor=page_one.get_facecolor())
    page_two.savefig(page_two_path, dpi=180, facecolor=page_two.get_facecolor())
    with PdfPages(pdf_path) as pdf:
        pdf.savefig(page_one, facecolor=page_one.get_facecolor())
        pdf.savefig(page_two, facecolor=page_two.get_facecolor())
    plt.close(page_one)
    plt.close(page_two)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=REPORTING_DIR,
        help="Directory for the two PNGs and two-page PDF.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    generate_package(parse_args().output_dir)
    print("Reporting package generated successfully.")
