"""Analyze the synthetic inventory sources and write the five required reports."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"

PRODUCT_FIELDS = [
    "sku", "product_name", "category", "supplier", "unit_cost",
    "lead_time_days", "reorder_point", "safety_stock",
    "annual_demand_estimate", "active_flag",
]
SOURCE_FIELDS = {
    "inventory_snapshot.csv": [
        "snapshot_date", "sku", "location", "zone", "system_qty",
        "physical_qty", "unit_cost",
    ],
    "product_master.csv": PRODUCT_FIELDS,
    "transactions.csv": [
        "transaction_id", "transaction_date", "sku", "location", "zone",
        "transaction_type", "quantity", "shift", "reference_id",
    ],
    "orders.csv": [
        "order_id", "order_date", "sku", "ordered_qty", "shipped_qty",
        "promised_date", "ship_date", "customer_segment",
    ],
    "cycle_counts.csv": [
        "count_id", "count_date", "sku", "location", "zone", "scheduled_flag",
        "completed_flag", "recount_flag", "variance_qty", "counter_team",
    ],
}

KPI_FIELDS = ["metric_name", "metric_value", "metric_unit", "calculation_note"]
PRIORITY_FIELDS = [
    "priority_rank", "sku", "product_name", "category", "supplier", "location",
    "zone", "system_qty", "physical_qty", "quantity_variance",
    "absolute_quantity_variance", "unit_cost", "adjustment_value",
    "average_daily_demand", "days_of_supply", "reorder_point", "safety_stock",
    "lead_time_days", "stockout_risk_flag", "variance_event_count",
    "priority_score", "recommended_count_frequency",
]
LOCATION_FIELDS = [
    "zone", "location", "sku_location_records", "total_adjustment_value",
    "average_inventory_accuracy", "stockout_risk_records",
    "variance_event_count", "recount_count", "priority_rank",
]
STOCKOUT_FIELDS = [
    "sku", "product_name", "category", "supplier", "location", "zone",
    "physical_qty", "average_daily_demand", "days_of_supply", "reorder_point",
    "safety_stock", "lead_time_days", "stockout_risk_reason",
    "recommended_action",
]
QUALITY_FIELDS = ["check_name", "status", "records_affected", "details"]


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        expected = SOURCE_FIELDS[name]
        if fields != expected:
            raise ValueError(f"{name} columns must be {expected}; found {fields}")
        return list(reader)


def write_csv(name: str, rows: list[dict[str, object]], fields: list[str]) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    with (OUTPUTS / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pct(numerator: float, denominator: float) -> float:
    return round(100 * numerator / denominator, 2) if denominator else 0.0


def ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def main() -> None:
    products_rows = read_csv("product_master.csv")
    products = {row["sku"]: row for row in products_rows}
    snapshots = read_csv("inventory_snapshot.csv")
    transactions = read_csv("transactions.csv")
    orders = read_csv("orders.csv")
    counts = read_csv("cycle_counts.csv")
    if not products or not snapshots or not transactions or not orders or not counts:
        raise ValueError("All five source files must contain data.")

    dates = sorted({row["snapshot_date"] for row in snapshots})
    period_start, period_end = date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])
    period_days = (period_end - period_start).days + 1
    locations = {
        row["location"]: (row["zone"], row["location"].split("-", 1)[-1])
        for row in snapshots
    }
    location_count_by_sku = defaultdict(int)
    for row in snapshots:
        location_count_by_sku[row["sku"]] += 1
    # Every SKU has one observation per location per day.
    for sku in location_count_by_sku:
        location_count_by_sku[sku] //= period_days

    pair = defaultdict(lambda: {
        "snapshot_count": 0, "latest_system": 0, "latest_physical": 0,
        "latest_cost": 0.0, "abs_variance": 0.0, "signed_variance": 0,
        "adjustment_value": 0.0, "variance_event_count": 0,
        "accuracy_numerator": 0.0, "accuracy_denominator": 0.0,
        "stockout_observations": 0,
    })
    snapshots_by_pair = defaultdict(list)
    location_stats = defaultdict(lambda: {
        "abs_variance": 0.0, "adjustment_value": 0.0, "accuracy_numerator": 0.0,
        "accuracy_denominator": 0.0, "variance_event_count": 0,
        "stockout_risk_records": 0, "recount_count": 0,
    })
    for row in snapshots:
        sku, location = row["sku"], row["location"]
        state = pair[(sku, location)]
        system = int(row["system_qty"])
        physical = int(row["physical_qty"])
        cost = float(row["unit_cost"])
        absolute_variance = abs(system - physical)
        state["snapshot_count"] += 1
        state["latest_system"] = system
        state["latest_physical"] = physical
        state["latest_cost"] = cost
        state["signed_variance"] = system - physical
        state["abs_variance"] += absolute_variance
        state["adjustment_value"] += absolute_variance * cost
        state["variance_event_count"] += absolute_variance > 0
        state["accuracy_numerator"] += max(physical, 1) - absolute_variance
        state["accuracy_denominator"] += max(physical, 1)
        snapshots_by_pair[(sku, location)].append((physical, cost))
        location_state = location_stats[location]
        location_state["abs_variance"] += absolute_variance
        location_state["adjustment_value"] += absolute_variance * cost
        location_state["accuracy_numerator"] += max(physical, 1) - absolute_variance
        location_state["accuracy_denominator"] += max(physical, 1)
        location_state["variance_event_count"] += absolute_variance > 0

    order_units_by_sku = defaultdict(int)
    for row in orders:
        order_units_by_sku[row["sku"]] += int(row["ordered_qty"])
    demand_by_sku = {
        sku: ratio(units, period_days)
        for sku, units in order_units_by_sku.items()
    }

    transaction_types = {row["transaction_type"] for row in transactions}
    required_transaction_types = {
        "RECEIPT", "PICK", "ADJUSTMENT", "TRANSFER_IN",
        "TRANSFER_OUT", "RETURN",
    }
    scheduled_counts = completed_counts = recounts = 0
    for row in counts:
        sku, location = row["sku"], row["location"]
        state = pair[(sku, location)]
        scheduled = row["scheduled_flag"].upper() == "Y"
        completed = scheduled and row["completed_flag"].upper() == "Y"
        if scheduled:
            scheduled_counts += 1
        if completed:
            completed_counts += 1
        if completed and row["recount_flag"].upper() == "Y":
            recounts += 1
        if row["recount_flag"].upper() == "Y":
            location_stats[location]["recount_count"] += 1

    def pair_demand(sku: str) -> float:
        return ratio(demand_by_sku.get(sku, 0.0), location_count_by_sku[sku])

    # Add derived stockout observations after demand is known.
    for (sku, location), state in pair.items():
        product = products[sku]
        demand = pair_demand(sku)
        lead = int(product["lead_time_days"])
        for physical, _cost in snapshots_by_pair[(sku, location)]:
            days_supply = ratio(physical, demand) if demand else float("inf")
            if physical <= int(product["reorder_point"]) or days_supply <= lead:
                state["stockout_observations"] += 1

    total_abs_variance = sum(state["abs_variance"] for state in pair.values())
    total_adjustment_value = sum(state["adjustment_value"] for state in pair.values())
    weighted_accuracy = ratio(
        sum(state["accuracy_numerator"] for state in pair.values()),
        sum(state["accuracy_denominator"] for state in pair.values()),
    )
    stockout_observations = sum(state["stockout_observations"] for state in pair.values())
    total_snapshots = len(snapshots)
    shipped_orders = [row for row in orders if int(row["shipped_qty"]) > 0]
    on_time_shipments = sum(
        date.fromisoformat(row["ship_date"]) <= date.fromisoformat(row["promised_date"])
        for row in shipped_orders
    )

    stockout_rows: list[dict[str, object]] = []
    for (sku, location), state in sorted(pair.items()):
        product = products[sku]
        demand = pair_demand(sku)
        days_supply = ratio(state["latest_physical"], demand) if demand else 999.0
        reorder = int(product["reorder_point"])
        lead = int(product["lead_time_days"])
        current_flag = state["latest_physical"] <= reorder or days_supply <= lead
        location_state = location_stats[location]
        location_state["stockout_risk_records"] += current_flag
        reason_parts = []
        if state["latest_physical"] <= reorder:
            reason_parts.append("physical quantity is at or below reorder point")
        if days_supply <= lead:
            reason_parts.append("days of supply is at or below lead time")
        reason = " and ".join(reason_parts) if reason_parts else "monitor demand and replenishment"
        stockout_rows.append({
            "sku": sku,
            "product_name": product["product_name"],
            "category": product["category"],
            "supplier": product["supplier"],
            "location": location,
            "zone": locations[location][0],
            "physical_qty": state["latest_physical"],
            "average_daily_demand": f"{demand:.2f}",
            "days_of_supply": f"{days_supply:.2f}",
            "reorder_point": reorder,
            "safety_stock": product["safety_stock"],
            "lead_time_days": lead,
            "stockout_risk_reason": reason,
            "recommended_action": (
                "Prioritize count and replenish" if current_flag
                else "Review reorder settings"
            ),
        })

    # Scores are deliberately decomposed in the documentation and SQL:
    # 35% adjustment value, 30% current stockout risk, 20% variance recurrence,
    # and 15% context (inventory value, lead time, and location recurrence).
    max_adjustment = max((state["adjustment_value"] for state in pair.values()), default=1.0)
    max_inventory_value = max(
        (state["latest_physical"] * state["latest_cost"] for state in pair.values()),
        default=1.0,
    )
    max_lead = max(int(product["lead_time_days"]) for product in products.values())
    max_location_recurrence = max(
        (stats["variance_event_count"] for stats in location_stats.values()), default=1
    )
    priority_rows: list[dict[str, object]] = []
    for (sku, location), state in pair.items():
        product = products[sku]
        demand = pair_demand(sku)
        days_supply = ratio(state["latest_physical"], demand) if demand else 999.0
        stockout_flag = state["latest_physical"] <= int(product["reorder_point"]) or days_supply <= int(product["lead_time_days"])
        adjustment_score = 100 * state["adjustment_value"] / max_adjustment
        stockout_score = 100.0 if stockout_flag else 0.0
        recurrence_score = 100 * state["variance_event_count"] / max(state["snapshot_count"], 1)
        location_score = 100 * location_stats[location]["variance_event_count"] / max_location_recurrence
        context_score = (
            40 * state["latest_physical"] * state["latest_cost"] / max_inventory_value
            + 30 * int(product["lead_time_days"]) / max_lead
            + 30 * location_score / 100
        )
        score = min(100.0, 0.35 * adjustment_score + 0.30 * stockout_score + 0.20 * recurrence_score + 0.15 * context_score)
        frequency = "Weekly" if stockout_flag or score >= 70 else "Biweekly" if score >= 40 else "Monthly"
        priority_rows.append({
            "_score": score,
            "_sku": sku,
            "_location": location,
            "priority_rank": 0,
            "sku": sku,
            "product_name": product["product_name"],
            "category": product["category"],
            "supplier": product["supplier"],
            "location": location,
            "zone": locations[location][0],
            "system_qty": state["latest_system"],
            "physical_qty": state["latest_physical"],
            "quantity_variance": state["signed_variance"],
            "absolute_quantity_variance": round(state["abs_variance"], 2),
            "unit_cost": product["unit_cost"],
            "adjustment_value": f"{state['adjustment_value']:.2f}",
            "average_daily_demand": f"{demand:.2f}",
            "days_of_supply": f"{days_supply:.2f}",
            "reorder_point": product["reorder_point"],
            "safety_stock": product["safety_stock"],
            "lead_time_days": product["lead_time_days"],
            "stockout_risk_flag": "Y" if stockout_flag else "N",
            "variance_event_count": state["variance_event_count"],
            "priority_score": f"{score:.2f}",
            "recommended_count_frequency": frequency,
        })

    priority_rows.sort(key=lambda row: (-row["_score"], row["_sku"], row["_location"]))
    for rank, row in enumerate(priority_rows, 1):
        row["priority_rank"] = rank
        for private_key in ("_score", "_sku", "_location"):
            del row[private_key]

    location_rows = []
    for location, stats in sorted(location_stats.items()):
        location_rows.append({
            "zone": locations[location][0],
            "location": location,
            "sku_location_records": sum(1 for _sku, loc in pair if loc == location),
            "total_adjustment_value": f"{stats['adjustment_value']:.2f}",
            "average_inventory_accuracy": f"{100 * ratio(stats['accuracy_numerator'], stats['accuracy_denominator']):.2f}",
            "stockout_risk_records": stats["stockout_risk_records"],
            "variance_event_count": stats["variance_event_count"],
            "recount_count": stats["recount_count"],
            "priority_rank": 0,
        })
    location_rows.sort(key=lambda row: (-float(row["total_adjustment_value"]), row["location"]))
    for rank, row in enumerate(location_rows, 1):
        row["priority_rank"] = rank

    kpis = [
        ("inventory_accuracy_pct", 100 * weighted_accuracy, "percent",
         "100 * (1 - sum(abs(system_qty - physical_qty)) / sum(max(physical_qty, 1)))"),
        ("adjustment_value", total_adjustment_value, "currency",
         "sum(abs(system_qty - physical_qty) * unit_cost) across snapshots"),
        ("stockout_rate_pct", pct(stockout_observations, total_snapshots), "percent",
         "stockout observations (physical <= reorder point or days of supply <= lead time) / snapshots"),
        ("days_of_supply", ratio(
            sum(state["latest_physical"] for state in pair.values()),
            sum(pair_demand(sku) for sku, _location in pair),
        ), "days", "latest physical quantity / average daily demand"),
        ("cycle_count_completion_pct", pct(completed_counts, scheduled_counts), "percent",
         "completed scheduled cycle counts / scheduled cycle counts"),
        ("recount_rate_pct", pct(recounts, completed_counts), "percent",
         "recounted completed cycle counts / completed cycle counts"),
        ("on_time_shipment_rate_pct", pct(on_time_shipments, len(shipped_orders)), "percent",
         "shipped orders with ship_date <= promised_date / shipped orders"),
        ("inventory_value", sum(state["latest_physical"] * state["latest_cost"] for state in pair.values()), "currency",
         "latest physical quantity * unit cost across SKU/location pairs"),
    ]
    kpi_rows = [{
        "metric_name": name,
        "metric_value": f"{float(value):.2f}",
        "metric_unit": unit,
        "calculation_note": note,
    } for name, value, unit, note in kpis]

    quality_rows: list[dict[str, object]] = []
    required_keys = {
        "inventory_snapshot.csv": ("snapshot_date", "sku", "location"),
        "product_master.csv": ("sku",),
        "transactions.csv": ("transaction_id",),
        "orders.csv": ("order_id",),
        "cycle_counts.csv": ("count_id",),
    }
    source_rows = {
        "inventory_snapshot.csv": snapshots,
        "product_master.csv": products_rows,
        "transactions.csv": transactions,
        "orders.csv": orders,
        "cycle_counts.csv": counts,
    }
    for filename, keys in required_keys.items():
        rows = source_rows[filename]
        nulls = sum(
            1 for row in rows for field in SOURCE_FIELDS[filename]
            if not row.get(field, "").strip()
        )
        duplicates = len(rows) - len({tuple(row.get(key, "") for key in keys) for row in rows})
        affected = nulls + duplicates
        quality_rows.append({
            "check_name": f"{filename} required fields and duplicates",
            "status": "PASS" if affected == 0 else "FAIL",
            "records_affected": affected,
            "details": f"required fields present; unique key: {', '.join(keys)}",
        })

    checks = [
        ("sku_reference_integrity",
         sum(row["sku"] not in products for row in snapshots + transactions + counts + orders),
         "all source SKUs exist in product master"),
        ("date_range_180_days", int(period_days != 180),
         f"observed period is {period_days} calendar days"),
        ("non_negative_inventory",
         sum(int(row["system_qty"]) < 0 or int(row["physical_qty"]) < 0 for row in snapshots),
         "system and physical quantities are non-negative"),
        ("snapshot_cost_matches_master",
         sum(round(float(row["unit_cost"]), 2) != round(float(products[row["sku"]]["unit_cost"]), 2) for row in snapshots),
         "snapshot unit costs match product master"),
        ("shipped_not_over_ordered",
         sum(int(row["shipped_qty"]) > int(row["ordered_qty"]) for row in orders),
         "shipped quantity does not exceed ordered quantity"),
        ("ship_date_not_before_order",
         sum(date.fromisoformat(row["ship_date"]) < date.fromisoformat(row["order_date"]) for row in orders),
         "shipment dates are not before order dates"),
        ("required_transaction_types", int(not required_transaction_types.issubset(transaction_types)),
         "transactions include RECEIPT, PICK, ADJUSTMENT, TRANSFER_IN, TRANSFER_OUT, and RETURN"),
        ("partial_shipments", int(not any(int(row["shipped_qty"]) < int(row["ordered_qty"]) for row in orders)),
         "orders include partial shipments"),
        ("delayed_shipments", int(not any(date.fromisoformat(row["ship_date"]) > date.fromisoformat(row["promised_date"]) for row in orders)),
         "orders include delayed shipments"),
        ("minimum_order_volume", int(len(orders) < 1500), f"{len(orders)} orders"),
        ("minimum_transaction_volume", int(len(transactions) < 8000), f"{len(transactions)} transactions"),
        ("minimum_cycle_count_volume", int(len(counts) < 450), f"{len(counts)} counts"),
    ]
    for check_name, affected, details in checks:
        quality_rows.append({
            "check_name": check_name,
            "status": "PASS" if affected == 0 else "FAIL",
            "records_affected": affected,
            "details": details,
        })

    write_csv("kpi_summary.csv", kpi_rows, KPI_FIELDS)
    write_csv("sku_risk_priorities.csv", priority_rows, PRIORITY_FIELDS)
    write_csv("location_variance_summary.csv", location_rows, LOCATION_FIELDS)
    write_csv(
        "stockout_risk_report.csv",
        [row for row in stockout_rows if row["recommended_action"] == "Prioritize count and replenish"],
        STOCKOUT_FIELDS,
    )
    write_csv("data_quality_checks.csv", quality_rows, QUALITY_FIELDS)
    print(
        f"Analyzed {len(products)} SKUs, {len(snapshots):,} snapshots, "
        f"{len(transactions):,} transactions, {len(orders):,} orders, and "
        f"{len(counts):,} cycle counts."
    )


if __name__ == "__main__":
    main()
