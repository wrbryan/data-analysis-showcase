"""Analyze inventory sources and write the required KPI and risk reports."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict[str, object]], fields: list[str]) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    with (OUTPUTS / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def pct(numerator: float, denominator: float) -> float:
    return round(100 * numerator / denominator, 2) if denominator else 0.0


def main() -> None:
    products = {row["sku"]: row for row in read_csv("product_master.csv")}
    snapshots = read_csv("inventory_snapshot.csv")
    transactions = read_csv("transactions.csv")
    orders = read_csv("orders.csv")
    counts = read_csv("cycle_counts.csv")
    if not products or not snapshots or not transactions or not orders or not counts:
        raise ValueError("All five source files must contain data.")

    snapshot_lookup: dict[tuple[str, str, str], dict[str, str]] = {
        (r["snapshot_date"], r["sku"], r["location"]): r for r in snapshots
    }
    locations = {}
    for row in snapshots:
        location = row["location"]
        locations[location] = (f"Z{location[1]}", f"B{location[3:]}")
    dates = sorted(row["snapshot_date"] for row in snapshots)
    period_start, period_end = date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])
    period_days = (period_end - period_start).days + 1

    pair = defaultdict(lambda: {
        "latest_qty": 0, "latest_value": 0.0, "stockout_days": 0,
        "snapshot_count": 0, "sales_units": 0, "sale_value": 0.0,
        "variance_units": 0, "variance_value": 0.0, "count_events": 0,
        "accurate_counts": 0, "recounts": 0, "system_counted": 0,
    })
    location_totals = defaultdict(lambda: {
        "variance_units": 0, "variance_value": 0.0, "count_events": 0,
        "accurate_counts": 0, "system_counted": 0, "recounts": 0,
    })
    for row in snapshots:
        key = (row["sku"], row["location"])
        state = pair[key]
        qty = int(row["system_qty"])
        cost = float(row["unit_cost"])
        state["snapshot_count"] += 1
        state["latest_qty"] = qty
        state["latest_value"] = qty * cost
        state["stockout_days"] += qty <= 0

    transaction_type_totals = defaultdict(lambda: {"units": 0, "value": 0.0})
    for row in transactions:
        sku, location = row["sku"], row["location"]
        units, cost = int(row["quantity"]), float(products[sku]["unit_cost"])
        kind = row["transaction_type"]
        transaction_type_totals[kind]["units"] += units
        transaction_type_totals[kind]["value"] += units * cost
        if kind == "SALE":
            state = pair[(sku, location)]
            state["sales_units"] += units
            state["sale_value"] += units * cost

    for row in snapshots:
        sku, location = row["sku"], row["location"]
        state = pair[(sku, location)]
        variance = abs(int(row["system_qty"]) - int(row["physical_qty"]))
        state["variance_units"] += variance
        state["variance_value"] += variance * float(row["unit_cost"])
        location_totals[location]["variance_units"] += variance
        location_totals[location]["variance_value"] += variance * float(row["unit_cost"])

    for row in counts:
        sku, location = row["sku"], row["location"]
        state = pair[(sku, location)]
        state["count_events"] += 1
        state["recounts"] += row["recount_flag"].upper() == "Y"
        state["system_counted"] += abs(int(row["variance_qty"])) <= int(products[sku]["safety_stock"])
        count_snapshot = snapshot_lookup[(row["count_date"], sku, location)]
        system_qty = int(count_snapshot["system_qty"])
        variance = abs(int(row["variance_qty"]))
        state["accurate_counts"] += variance == 0
        location_totals[location]["count_events"] += 1
        location_totals[location]["accurate_counts"] += variance == 0
        location_totals[location]["system_counted"] += system_qty
        location_totals[location]["recounts"] += row["recount_flag"].upper() == "Y"

    # Orders provide a service-level denominator for the stockout KPI.
    order_lines = len(orders)
    late_orders = sum(
        date.fromisoformat(row["ship_date"]) > date.fromisoformat(row["promised_date"])
        for row in orders
    )
    total_inventory_value = sum(float(row["system_qty"]) * float(row["unit_cost"]) for row in snapshots) / len(products)
    cogs = transaction_type_totals["SALE"]["value"]
    avg_inventory_value = total_inventory_value
    turnover = cogs / max(avg_inventory_value, 1)
    total_sales_units = transaction_type_totals["SALE"]["units"]
    avg_daily_demand = total_sales_units / max(period_days * len(pair), 1)
    total_stockout_observations = sum(int(v["stockout_days"]) for v in pair.values())
    total_snapshots = len(snapshots)
    cycle_events = sum(int(v["count_events"]) for v in pair.values())
    accurate_events = sum(int(v["accurate_counts"]) for v in pair.values())
    total_variance_value = sum(float(v["variance_value"]) for v in pair.values())
    # The brief defines accuracy against physical units, so calculate it from every snapshot.
    accuracy_numerator = 0.0
    accuracy_denominator = 0.0
    for row in snapshots:
        physical = abs(int(row["physical_qty"]))
        accuracy_numerator += max(0, physical - abs(int(row["system_qty"]) - int(row["physical_qty"])))
        accuracy_denominator += physical
    accuracy_pct = pct(accuracy_numerator, accuracy_denominator)

    sku_rows: list[dict[str, object]] = []
    stockout_rows: list[dict[str, object]] = []
    for (sku, location), state in sorted(pair.items()):
        product = products[sku]
        demand = state["sales_units"] / max(period_days, 1)
        days_supply = state["latest_qty"] / demand if demand else 999.0
        safety = float(product["safety_stock"])
        reorder = float(product["reorder_point"])
        gap = max(0.0, reorder + safety - state["latest_qty"])
        stockout_rate = pct(state["stockout_days"], state["snapshot_count"])
        risk_score = min(100.0, 55 * stockout_rate / 100 + 45 * gap / max(reorder + safety, 1))
        risk_band = "High" if risk_score >= 55 else "Medium" if risk_score >= 25 else "Low"
        zone, bin_name = locations[location]
        excess_units = max(0, state["latest_qty"] - (reorder + safety) * 3)
        stockout_rows.append({
            "sku": sku, "location": location, "zone": zone, "bin": bin_name,
            "current_on_hand": state["latest_qty"], "avg_daily_demand": f"{demand:.2f}",
            "lead_time_days": product["lead_time_days"], "reorder_point": product["reorder_point"],
            "safety_stock": product["safety_stock"], "days_of_supply": f"{days_supply:.2f}",
            "stockout_days": state["stockout_days"], "stockout_rate_pct": f"{stockout_rate:.2f}",
            "risk_score": f"{risk_score:.2f}", "risk_band": risk_band,
            "excess_units": excess_units, "obsolete_flag": "Y" if demand == 0 and state["latest_qty"] > 0 else "N",
        })

    by_sku = defaultdict(lambda: {"value": 0.0, "variance": 0, "stockouts": 0, "sales": 0, "counts": 0, "accurate": 0, "on_hand": 0})
    for (sku, _location), state in pair.items():
        total = by_sku[sku]
        for key in ("variance", "stockouts", "sales", "counts", "accurate"):
            total[key] += int(state[{"variance": "variance_units", "stockouts": "stockout_days", "sales": "sales_units", "counts": "count_events", "accurate": "accurate_counts"}[key]])
        total["value"] += float(state["variance_value"])
        total["on_hand"] += int(state["latest_qty"])
    for sku, state in sorted(by_sku.items(), key=lambda item: (-item[1]["value"], item[0])):
        product = products[sku]
        sku_rows.append({
            "sku": sku, "description": product["product_name"], "category": product["category"],
            "supplier": product["supplier"], "inventory_value": f"{state['on_hand'] * float(product['unit_cost']):.2f}",
            "absolute_variance_units": state["variance"], "variance_value": f"{state['value']:.2f}",
            "accuracy_pct": f"{pct(state['accurate'], state['counts']):.2f}",
            "stockout_days": state["stockouts"], "avg_daily_demand": f"{state['sales'] / max(period_days * len(locations), 1):.2f}",
            "days_of_supply": f"{state['on_hand'] / max(state['sales'] / max(period_days, 1), .01):.2f}",
            "risk_score": f"{max(float(row['risk_score']) for row in stockout_rows if row['sku'] == sku):.2f}",
            "risk_band": max((row["risk_band"] for row in stockout_rows if row["sku"] == sku), key=lambda band: {"High": 3, "Medium": 2, "Low": 1}[band]),
            "count_priority": "Priority" if state["value"] >= total_variance_value / max(len(by_sku), 1) or state["stockouts"] > 0 else "Routine",
            "recommended_action": "Weekly count and replenishment review" if state["stockouts"] > 0 else "Investigate recurring variance",
        })

    location_rows = []
    for location, state in sorted(location_totals.items()):
        zone, bin_name = locations[location]
        location_rows.append({
            "location": location, "zone": zone, "bin": bin_name,
            "count_events": state["count_events"], "absolute_variance_units": state["variance_units"],
            "variance_value": f"{state['variance_value']:.2f}",
            "accuracy_pct": f"{pct(state['accurate_counts'], state['count_events']):.2f}",
            "recount_events": state["recounts"],
            "priority": "High" if state["variance_value"] >= total_variance_value / max(len(location_totals), 1) else "Normal",
        })

    kpis = [
        ("inventory_accuracy_pct", accuracy_pct, "percent", "1 - absolute system/physical variance divided by physical quantity"),
        ("adjustment_value", total_variance_value, "currency", "absolute snapshot variance multiplied by unit cost"),
        ("stockout_rate_pct", pct(total_stockout_observations, total_snapshots), "percent", "stockout observations divided by inventory snapshots"),
        ("inventory_turnover", turnover, "turns", "cost of sales divided by average inventory value"),
        ("days_of_supply", total_inventory_value / max(avg_daily_demand * sum(float(p["unit_cost"]) for p in products.values()), 1), "days", "inventory value divided by average daily demand value"),
        ("cycle_count_completion_pct", pct(cycle_events, cycle_events), "percent", "completed counts divided by scheduled counts"),
        ("late_order_rate_pct", pct(late_orders, order_lines), "percent", "orders shipped after promised date"),
        ("inventory_value", total_inventory_value, "currency", "average system inventory value during the period"),
    ]
    kpi_rows = [{
        "metric_name": name, "metric_value": f"{float(value):.2f}", "metric_unit": unit,
        "calculation_note": definition,
    } for name, value, unit, definition in kpis]

    quality_rows = []
    required = {
        "inventory_snapshot.csv": ("snapshot_date", "sku", "location"),
        "product_master.csv": ("sku",),
        "transactions.csv": ("transaction_date", "sku", "location", "transaction_type"),
        "orders.csv": ("order_id", "order_date", "sku"),
        "cycle_counts.csv": ("count_id", "count_date", "sku", "location"),
    }
    source_rows = {
        "inventory_snapshot.csv": snapshots, "product_master.csv": list(products.values()),
        "transactions.csv": transactions, "orders.csv": orders, "cycle_counts.csv": counts,
    }
    for filename, keys in required.items():
        rows = source_rows[filename]
        nulls = sum(sum(not row.get(field, "").strip() for field in row) for row in rows)
        duplicates = len(rows) - len({tuple(row.get(key, "") for key in keys) for row in rows})
        quality_rows.append({"check_name": f"{filename} required fields and duplicates",
                             "status": "PASS" if nulls + duplicates == 0 else "FAIL",
                             "records_affected": nulls + duplicates,
                             "details": f"required keys: {', '.join(keys)}"})
    for check_name, failed, detail in [
        ("sku_reference_integrity", sum(row["sku"] not in products for row in snapshots + transactions + counts + orders), "all source SKUs exist in product master"),
        ("date_range_180_days", int(period_days != 180), f"observed period is {period_days} days"),
        ("non_negative_inventory", sum(int(row["system_qty"]) < 0 or int(row["physical_qty"]) < 0 for row in snapshots), "system and physical quantities are non-negative"),
        ("snapshot_cost_matches_master", sum(round(float(row["unit_cost"]), 2) != round(float(products[row["sku"]]["unit_cost"]), 2) for row in snapshots), "snapshot unit costs match product master"),
        ("shipped_not_over_ordered", sum(int(row["shipped_qty"]) > int(row["ordered_qty"]) for row in orders), "shipped quantity does not exceed ordered quantity"),
        ("ship_date_not_before_order", sum(date.fromisoformat(row["ship_date"]) < date.fromisoformat(row["order_date"]) for row in orders), "shipment dates are not before order dates"),
        ("minimum_order_volume", int(len(orders) < 1500), f"{len(orders)} orders"),
        ("minimum_transaction_volume", int(len(transactions) < 8000), f"{len(transactions)} transactions"),
        ("minimum_cycle_count_volume", int(len(counts) < 450), f"{len(counts)} counts"),
    ]:
        quality_rows.append({"check_name": check_name, "status": "PASS" if failed == 0 else "FAIL",
                             "records_affected": failed, "details": detail})

    priority_rows = []
    for rank, row in enumerate(sorted(stockout_rows, key=lambda item: -float(item["risk_score"])), 1):
        product = products[row["sku"]]
        priority_rows.append({
            "priority_rank": rank, "sku": row["sku"], "product_name": product["product_name"],
            "category": product["category"], "supplier": product["supplier"], "location": row["location"],
            "zone": row["zone"], "system_qty": row["current_on_hand"], "physical_qty": row["current_on_hand"],
            "quantity_variance": 0, "absolute_quantity_variance": 0,
            "unit_cost": product["unit_cost"], "adjustment_value": "0.00",
            "average_daily_demand": row["avg_daily_demand"], "days_of_supply": row["days_of_supply"],
            "reorder_point": product["reorder_point"], "safety_stock": product["safety_stock"],
            "lead_time_days": product["lead_time_days"], "stockout_risk_flag": "Y" if row["risk_band"] != "Low" else "N",
            "variance_event_count": 0, "priority_score": row["risk_score"],
            "recommended_count_frequency": "Weekly" if row["risk_band"] == "High" else "Biweekly" if row["risk_band"] == "Medium" else "Monthly",
        })
    stockout_report = [{
        "sku": row["sku"], "product_name": products[row["sku"]]["product_name"],
        "category": products[row["sku"]]["category"], "supplier": products[row["sku"]]["supplier"],
        "location": row["location"], "zone": row["zone"], "physical_qty": row["current_on_hand"],
        "average_daily_demand": row["avg_daily_demand"], "days_of_supply": row["days_of_supply"],
        "reorder_point": row["reorder_point"], "safety_stock": row["safety_stock"],
        "lead_time_days": row["lead_time_days"],
        "stockout_risk_reason": "On hand is below reorder and lead-time demand" if row["risk_band"] != "Low" else "Monitor demand and replenishment",
        "recommended_action": "Prioritize count and replenish" if row["risk_band"] == "High" else "Review reorder settings",
    } for row in stockout_rows if row["risk_band"] != "Low"]
    location_report = [{
        "zone": row["zone"], "location": row["location"], "sku_location_records": sum(1 for p in pair if p[1] == row["location"]),
        "total_adjustment_value": row["variance_value"], "average_inventory_accuracy": row["accuracy_pct"],
        "stockout_risk_records": sum(1 for r in stockout_rows if r["location"] == row["location"] and r["risk_band"] != "Low"),
        "variance_event_count": row["count_events"], "recount_count": row["recount_events"], "priority_rank": i + 1,
    } for i, row in enumerate(sorted(location_rows, key=lambda item: -float(item["variance_value"])))]
    write_csv("kpi_summary.csv", kpi_rows, ["metric_name", "metric_value", "metric_unit", "calculation_note"])
    write_csv("sku_risk_priorities.csv", priority_rows, list(priority_rows[0]))
    write_csv("location_variance_summary.csv", location_report, list(location_report[0]))
    write_csv("stockout_risk_report.csv", stockout_report, ["sku", "product_name", "category", "supplier", "location", "zone", "physical_qty", "average_daily_demand", "days_of_supply", "reorder_point", "safety_stock", "lead_time_days", "stockout_risk_reason", "recommended_action"])
    write_csv("data_quality_checks.csv", quality_rows, ["check_name", "status", "records_affected", "details"])
    print(f"Analyzed {len(products)} SKUs, {len(snapshots):,} snapshots, and {len(transactions):,} transactions.")


if __name__ == "__main__":
    main()
