"""Publish complementary SKU replenishment and SKU/location count queues.

The replenishment queue aggregates the latest inventory position across all
locations for each SKU.  The count queue remains at SKU/location grain and
uses variance, recount, and transaction-control signals only; a low bin never
becomes an enterprise SKU stockout by itself.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "generated"
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
REPLENISHMENT_FIELDS = [
    "priority_rank", "sku", "product_name", "category", "supplier",
    "location_count", "total_system_qty", "total_physical_qty",
    "total_quantity_variance", "total_absolute_quantity_variance", "unit_cost",
    "inventory_value", "adjustment_exposure", "average_daily_demand",
    "days_of_supply", "reorder_point", "safety_stock", "lead_time_days",
    "reorder_point_trigger", "safety_stock_trigger", "lead_time_trigger",
    "materiality_flag", "replenishment_tier", "replenishment_reason",
    "action_flag", "priority_score",
]
COUNT_PRIORITY_FIELDS = [
    "priority_rank", "sku", "product_name", "category", "location", "zone",
    "latest_system_qty", "latest_physical_qty", "quantity_variance",
    "absolute_quantity_variance", "unit_cost", "inventory_value",
    "location_adjustment_exposure", "variance_event_count",
    "recurring_variance", "count_records", "recount_count", "recount_rate",
    "transaction_volume", "location_recurrence_flag", "control_tier",
    "control_reason", "count_action_flag", "priority_score",
    "recommended_count_frequency",
]
LOCATION_FIELDS = [
    "zone", "location", "sku_location_records", "total_adjustment_value",
    "average_inventory_accuracy", "recurring_variance_pairs",
    "recount_count", "transaction_volume", "priority_rank",
]
STOCKOUT_FIELDS = [
    "priority_rank", "sku", "product_name", "category", "supplier",
    "total_physical_qty", "average_daily_demand", "days_of_supply",
    "reorder_point", "safety_stock", "lead_time_days", "materiality_flag",
    "replenishment_tier", "replenishment_reason", "action_flag",
    "stockout_risk_reason", "recommended_action",
]
QUALITY_FIELDS = ["check_name", "status", "records_affected", "details"]


def read_csv(name: str) -> list[dict[str, str]]:
    path = DATA / name
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing; run generate_synthetic_data.py first."
        )
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if fields != SOURCE_FIELDS[name]:
            raise ValueError(f"{name} columns must be {SOURCE_FIELDS[name]}; found {fields}")
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


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def main() -> None:
    products_rows = read_csv("product_master.csv")
    products = {row["sku"]: row for row in products_rows}
    snapshots = read_csv("inventory_snapshot.csv")
    transactions = read_csv("transactions.csv")
    orders = read_csv("orders.csv")
    counts = read_csv("cycle_counts.csv")
    if not products or not snapshots or not transactions or not orders or not counts:
        raise ValueError("All five generated source files must contain data.")

    dates = sorted({row["snapshot_date"] for row in snapshots})
    period_start, period_end = date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])
    period_days = (period_end - period_start).days + 1
    locations = {row["location"]: row["zone"] for row in snapshots}
    pair = defaultdict(lambda: {
        "latest_date": "", "latest_system": 0, "latest_physical": 0,
        "latest_cost": 0.0, "signed_variance": 0, "abs_variance": 0.0,
        "adjustment_value": 0.0, "variance_event_count": 0,
        "accuracy_numerator": 0.0, "accuracy_denominator": 0.0,
    })
    sku_state = defaultdict(lambda: {
        "total_system": 0, "total_physical": 0, "total_variance": 0,
        "total_abs_variance": 0.0, "inventory_value": 0.0,
        "adjustment_exposure": 0.0, "historical_stockout_count": 0,
    })
    snapshots_by_pair = defaultdict(list)
    location_stats = defaultdict(lambda: {
        "adjustment_value": 0.0, "accuracy_numerator": 0.0,
        "accuracy_denominator": 0.0, "transaction_volume": 0,
        "recurring_variance_pairs": 0, "recount_count": 0,
    })
    for row in snapshots:
        sku, location = row["sku"], row["location"]
        system, physical, cost = int(row["system_qty"]), int(row["physical_qty"]), float(row["unit_cost"])
        absolute_variance = abs(system - physical)
        state = pair[(sku, location)]
        state["latest_date"] = row["snapshot_date"]
        state["latest_system"] = system
        state["latest_physical"] = physical
        state["latest_cost"] = cost
        state["signed_variance"] = system - physical
        state["abs_variance"] += absolute_variance
        state["adjustment_value"] += absolute_variance * cost
        state["variance_event_count"] += int(absolute_variance > 0)
        state["accuracy_numerator"] += max(physical, 1) - absolute_variance
        state["accuracy_denominator"] += max(physical, 1)
        snapshots_by_pair[(sku, location)].append((physical, cost))
        aggregate = sku_state[sku]
        aggregate["total_system"] += system
        aggregate["total_physical"] += physical
        aggregate["total_variance"] += system - physical
        aggregate["total_abs_variance"] += absolute_variance
        aggregate["adjustment_exposure"] += absolute_variance * cost
        location_state = location_stats[location]
        location_state["adjustment_value"] += absolute_variance * cost
        location_state["accuracy_numerator"] += max(physical, 1) - absolute_variance
        location_state["accuracy_denominator"] += max(physical, 1)

    transaction_volume_by_pair = defaultdict(int)
    for row in transactions:
        transaction_volume_by_pair[(row["sku"], row["location"])] += 1
        location_stats[row["location"]]["transaction_volume"] += 1

    # Rebuild the SKU position from the latest record in each location.  The
    # exposure fields above intentionally remain cumulative across the source
    # period, while on-hand/value fields are current operational position.
    for sku in sku_state:
        aggregate = sku_state[sku]
        aggregate["total_system"] = sum(
            state["latest_system"] for (pair_sku, _location), state in pair.items()
            if pair_sku == sku
        )
        aggregate["total_physical"] = sum(
            state["latest_physical"] for (pair_sku, _location), state in pair.items()
            if pair_sku == sku
        )
        aggregate["total_variance"] = sum(
            state["signed_variance"] for (pair_sku, _location), state in pair.items()
            if pair_sku == sku
        )
        aggregate["total_abs_variance"] = sum(
            abs(state["signed_variance"]) for (pair_sku, _location), state in pair.items()
            if pair_sku == sku
        )

    order_units_by_sku = defaultdict(int)
    for row in orders:
        order_units_by_sku[row["sku"]] += int(row["ordered_qty"])
    demand_by_sku = {
        sku: ratio(units, period_days) for sku, units in order_units_by_sku.items()
    }

    # Historical exposure is retained as a KPI, but it is not used to infer
    # SKU stockout risk from one low location.
    historical_stockout_observations = 0
    for (sku, location), state in pair.items():
        product = products[sku]
        daily_demand = demand_by_sku.get(sku, 0.0)
        for physical, _cost in snapshots_by_pair[(sku, location)]:
            days_supply = ratio(physical, daily_demand)
            trigger = physical <= int(product["reorder_point"]) or days_supply <= int(product["lead_time_days"])
            historical_stockout_observations += int(trigger)

    count_state = defaultdict(lambda: {
        "count_records": 0, "completed_count": 0, "recount_count": 0,
        "variance_abs": 0,
    })
    scheduled_counts = completed_counts = recounts = 0
    for row in counts:
        key = (row["sku"], row["location"])
        scheduled = row["scheduled_flag"].upper() == "Y"
        completed = scheduled and row["completed_flag"].upper() == "Y"
        recount = completed and row["recount_flag"].upper() == "Y"
        scheduled_counts += int(scheduled)
        completed_counts += int(completed)
        recounts += int(recount)
        state = count_state[key]
        state["count_records"] += int(scheduled)
        state["completed_count"] += int(completed)
        state["recount_count"] += int(recount)
        state["variance_abs"] += abs(int(row["variance_qty"]))
        location_stats[row["location"]]["recount_count"] += int(recount)

    recurring_location_pairs = {
        key: int(state["variance_event_count"] >= 2)
        for key, state in pair.items()
    }
    for (sku, location), recurring in recurring_location_pairs.items():
        location_stats[location]["recurring_variance_pairs"] += recurring
    location_recurrence = {
        location: stats["recurring_variance_pairs"] >= 2
        for location, stats in location_stats.items()
    }

    # SKU-grain materiality and replenishment tiering.
    sku_values = []
    for sku, aggregate in sku_state.items():
        cost = float(products[sku]["unit_cost"])
        sku_values.append({
            "inventory_value": aggregate["total_physical"] * cost,
            "adjustment_exposure": aggregate["adjustment_exposure"],
            "unit_cost": cost,
        })
    materiality_thresholds = {
        key: percentile([row[key] for row in sku_values], 0.75)
        for key in ("inventory_value", "adjustment_exposure", "unit_cost")
    }
    sku_metrics = {}
    for sku, aggregate in sku_state.items():
        product = products[sku]
        cost = float(product["unit_cost"])
        demand = demand_by_sku.get(sku, 0.0)
        total_physical = aggregate["total_physical"]
        days_supply = ratio(total_physical, demand)
        inventory_value = total_physical * cost
        materiality = (
            inventory_value >= materiality_thresholds["inventory_value"]
            or aggregate["adjustment_exposure"] >= materiality_thresholds["adjustment_exposure"]
            or cost >= materiality_thresholds["unit_cost"]
        )
        reorder_trigger = total_physical <= int(product["reorder_point"])
        safety_trigger = total_physical <= int(product["safety_stock"])
        lead_trigger = days_supply <= int(product["lead_time_days"])
        current_trigger = reorder_trigger or lead_trigger
        if total_physical == 0 or days_supply <= 0.25 * int(product["lead_time_days"]):
            tier = "Critical"
            reason = "Critical: total physical quantity is zero or days of supply <= 0.25 lead time"
        elif safety_trigger and lead_trigger and materiality:
            tier = "Critical"
            reason = "Critical: total quantity <= safety stock with materiality and lead-time trigger"
        elif reorder_trigger and lead_trigger:
            tier = "High"
            reason = "High: total quantity <= reorder point and days of supply <= lead time"
        elif current_trigger or (materiality and aggregate["adjustment_exposure"] > 0):
            tier = "Watch"
            reason = "Watch: total quantity or days-of-supply policy trigger, or material exposure"
        else:
            tier = "Routine"
            reason = "Routine: SKU-level quantity and supply policy triggers are not met"
        sku_metrics[sku] = {
            "demand": demand, "days_supply": days_supply, "inventory_value": inventory_value,
            "materiality": materiality, "reorder_trigger": reorder_trigger,
            "safety_trigger": safety_trigger, "lead_trigger": lead_trigger,
            "tier": tier, "reason": reason, "action": tier in {"Critical", "High"},
            "current_trigger": current_trigger,
        }

    sku_tier_counts = defaultdict(int)
    for metrics in sku_metrics.values():
        sku_tier_counts[metrics["tier"]] += 1
    max_sku_adjustment = max((a["adjustment_exposure"] for a in sku_state.values()), default=1.0)
    max_sku_inventory = max((m["inventory_value"] for m in sku_metrics.values()), default=1.0)
    replenishment_rows = []
    for sku in sorted(sku_state):
        aggregate, product, metrics = sku_state[sku], products[sku], sku_metrics[sku]
        score = min(100.0, 45 * aggregate["adjustment_exposure"] / max_sku_adjustment
                    + 35 * int(metrics["current_trigger"])
                    + 20 * metrics["inventory_value"] / max_sku_inventory)
        replenishment_rows.append({
            "_score": score, "_sku": sku, "priority_rank": 0, "sku": sku,
            "product_name": product["product_name"], "category": product["category"],
            "supplier": product["supplier"], "location_count": len(locations),
            "total_system_qty": aggregate["total_system"],
            "total_physical_qty": aggregate["total_physical"],
            "total_quantity_variance": aggregate["total_variance"],
            "total_absolute_quantity_variance": round(aggregate["total_abs_variance"], 2),
            "unit_cost": product["unit_cost"],
            "inventory_value": f"{metrics['inventory_value']:.2f}",
            "adjustment_exposure": f"{aggregate['adjustment_exposure']:.2f}",
            "average_daily_demand": f"{metrics['demand']:.2f}",
            "days_of_supply": f"{metrics['days_supply']:.2f}",
            "reorder_point": product["reorder_point"], "safety_stock": product["safety_stock"],
            "lead_time_days": product["lead_time_days"],
            "reorder_point_trigger": "Y" if metrics["reorder_trigger"] else "N",
            "safety_stock_trigger": "Y" if metrics["safety_trigger"] else "N",
            "lead_time_trigger": "Y" if metrics["lead_trigger"] else "N",
            "materiality_flag": "Y" if metrics["materiality"] else "N",
            "replenishment_tier": metrics["tier"], "replenishment_reason": metrics["reason"],
            "action_flag": "Y" if metrics["action"] else "N", "priority_score": f"{score:.2f}",
        })
    replenishment_rows.sort(key=lambda row: (-row["_score"], row["_sku"]))
    for rank, row in enumerate(replenishment_rows, 1):
        row["priority_rank"] = rank
        del row["_score"], row["_sku"]

    # Location-control tiering intentionally does not include SKU replenishment
    # tier or a stockout flag.
    max_pair_adjustment = max((state["adjustment_value"] for state in pair.values()), default=1.0)
    max_pair_transactions = max(transaction_volume_by_pair.values(), default=1)
    count_rows = []
    count_tier_counts = defaultdict(int)
    for (sku, location), state in sorted(pair.items()):
        product, cstate = products[sku], count_state[(sku, location)]
        abs_latest = abs(int(state["signed_variance"]))
        recurring = int(state["variance_event_count"]) >= 2
        recount_rate = ratio(cstate["recount_count"], cstate["completed_count"])
        loc_repeat = location_recurrence[location]
        if recurring and abs_latest >= 2 and cstate["recount_count"] >= 3 and loc_repeat:
            tier = "Critical"
            reason = "Critical: recurring variance, large latest discrepancy, and repeated recounts in a recurring-variance location"
        elif recurring and (cstate["recount_count"] >= 2 or state["adjustment_value"] >= max_pair_adjustment * 0.75):
            tier = "High"
            reason = "High: recurring SKU/location variance with repeated recount or material adjustment exposure"
        elif recurring or cstate["recount_count"] > 0 or abs_latest > 0:
            tier = "Watch"
            reason = "Watch: variance or recount pattern warrants monitoring"
        else:
            tier = "Routine"
            reason = "Routine: no recurring variance or recount pattern"
        count_tier_counts[tier] += 1
        score = min(100.0, 45 * state["adjustment_value"] / max_pair_adjustment
                    + 25 * int(recurring) + 20 * min(recount_rate / 0.5, 1)
                    + 10 * transaction_volume_by_pair[(sku, location)] / max_pair_transactions)
        count_rows.append({
            "_score": score, "_key": (sku, location), "priority_rank": 0, "sku": sku,
            "product_name": product["product_name"], "category": product["category"],
            "location": location, "zone": locations[location],
            "latest_system_qty": state["latest_system"], "latest_physical_qty": state["latest_physical"],
            "quantity_variance": state["signed_variance"], "absolute_quantity_variance": abs_latest,
            "unit_cost": product["unit_cost"],
            "inventory_value": f"{state['latest_physical'] * float(product['unit_cost']):.2f}",
            "location_adjustment_exposure": f"{state['adjustment_value']:.2f}",
            "variance_event_count": state["variance_event_count"],
            "recurring_variance": "Y" if recurring else "N",
            "count_records": cstate["count_records"], "recount_count": cstate["recount_count"],
            "recount_rate": f"{100 * recount_rate:.2f}",
            "transaction_volume": transaction_volume_by_pair[(sku, location)],
            "location_recurrence_flag": "Y" if loc_repeat else "N",
            "control_tier": tier, "control_reason": reason,
            "count_action_flag": "Y" if tier in {"Critical", "High"} else "N",
            "priority_score": f"{score:.2f}",
            "recommended_count_frequency": (
                "Weekly" if tier == "Critical" else
                "Biweekly" if tier == "High" else
                "Monthly" if tier == "Watch" else "Quarterly"
            ),
        })
    count_rows.sort(key=lambda row: (-row["_score"], row["sku"], row["location"]))
    for rank, row in enumerate(count_rows, 1):
        row["priority_rank"] = rank
        del row["_score"], row["_key"]

    stockout_rows = []
    for row in replenishment_rows:
        if row["action_flag"] != "Y":
            continue
        stockout_rows.append({
            "priority_rank": row["priority_rank"], "sku": row["sku"],
            "product_name": row["product_name"], "category": row["category"],
            "supplier": row["supplier"], "total_physical_qty": row["total_physical_qty"],
            "average_daily_demand": row["average_daily_demand"], "days_of_supply": row["days_of_supply"],
            "reorder_point": row["reorder_point"], "safety_stock": row["safety_stock"],
            "lead_time_days": row["lead_time_days"], "materiality_flag": row["materiality_flag"],
            "replenishment_tier": row["replenishment_tier"],
            "replenishment_reason": row["replenishment_reason"], "action_flag": row["action_flag"],
            "stockout_risk_reason": "SKU-level total on-hand compared with reorder point and lead time",
            "recommended_action": "Validate supply position and expedite replenishment",
        })

    location_rows = []
    for location, stats in sorted(location_stats.items()):
        location_rows.append({
            "zone": locations[location], "location": location,
            "sku_location_records": sum(loc == location for _sku, loc in pair),
            "total_adjustment_value": f"{stats['adjustment_value']:.2f}",
            "average_inventory_accuracy": f"{100 * ratio(stats['accuracy_numerator'], stats['accuracy_denominator']):.2f}",
            "recurring_variance_pairs": stats["recurring_variance_pairs"],
            "recount_count": stats["recount_count"],
            "transaction_volume": stats["transaction_volume"], "priority_rank": 0,
        })
    location_rows.sort(key=lambda row: (-float(row["total_adjustment_value"]), row["location"]))
    for rank, row in enumerate(location_rows, 1):
        row["priority_rank"] = rank

    weighted_accuracy = ratio(
        sum(state["accuracy_numerator"] for state in pair.values()),
        sum(state["accuracy_denominator"] for state in pair.values()),
    )
    shipped_orders = [row for row in orders if int(row["shipped_qty"]) > 0]
    on_time_shipments = sum(
        date.fromisoformat(row["ship_date"]) <= date.fromisoformat(row["promised_date"])
        for row in shipped_orders
    )
    kpis = [
        ("inventory_accuracy_pct", 100 * weighted_accuracy, "percent", "weighted latest-period accuracy"),
        ("adjustment_value", sum(a["adjustment_exposure"] for a in sku_state.values()), "currency", "cumulative adjustment exposure across snapshots"),
        ("historical_stockout_observation_rate_pct", pct(historical_stockout_observations, len(snapshots)), "percent", "historical broad trigger / all snapshots; not an enterprise current queue"),
        ("replenishment_sku_count", len(replenishment_rows), "SKUs", "one row per SKU across all locations"),
        ("count_priority_sku_location_count", len(count_rows), "SKU/location records", "all latest SKU/location pairs retained"),
        ("replenishment_critical_count", sku_tier_counts["Critical"], "SKUs", "SKU-level replenishment tier"),
        ("replenishment_high_count", sku_tier_counts["High"], "SKUs", "SKU-level replenishment tier"),
        ("replenishment_watch_count", sku_tier_counts["Watch"], "SKUs", "SKU-level replenishment tier"),
        ("replenishment_routine_count", sku_tier_counts["Routine"], "SKUs", "SKU-level replenishment tier"),
        ("replenishment_critical_high_rate_pct", pct(sku_tier_counts["Critical"] + sku_tier_counts["High"], len(replenishment_rows)), "percent", "Critical + High SKUs / all SKUs"),
        ("count_priority_critical_count", count_tier_counts["Critical"], "SKU/location records", "SKU/location control tier"),
        ("count_priority_high_count", count_tier_counts["High"], "SKU/location records", "SKU/location control tier"),
        ("count_priority_watch_count", count_tier_counts["Watch"], "SKU/location records", "SKU/location control tier"),
        ("count_priority_routine_count", count_tier_counts["Routine"], "SKU/location records", "SKU/location control tier"),
        ("count_priority_critical_high_rate_pct", pct(count_tier_counts["Critical"] + count_tier_counts["High"], len(count_rows)), "percent", "Critical + High SKU/location records / all pairs"),
        ("materiality_p75_inventory_value", materiality_thresholds["inventory_value"], "currency", "PERCENTILE_CONT(0.75) across latest SKU inventory value"),
        ("materiality_p75_adjustment_exposure", materiality_thresholds["adjustment_exposure"], "currency", "PERCENTILE_CONT(0.75) across SKU adjustment exposure"),
        ("cycle_count_completion_pct", pct(completed_counts, scheduled_counts), "percent", "completed scheduled cycle counts / scheduled counts"),
        ("recount_rate_pct", pct(recounts, completed_counts), "percent", "recounted completed counts / completed counts"),
        ("on_time_shipment_rate_pct", pct(on_time_shipments, len(shipped_orders)), "percent", "shipped orders on or before promise"),
        ("inventory_value", sum(float(row["inventory_value"]) for row in replenishment_rows), "currency", "latest total physical quantity * unit cost"),
    ]
    kpi_rows = [{
        "metric_name": name, "metric_value": f"{float(value):.2f}",
        "metric_unit": unit, "calculation_note": note,
    } for name, value, unit, note in kpis]

    quality_rows: list[dict[str, object]] = []
    required_keys = {
        "inventory_snapshot.csv": ("snapshot_date", "sku", "location"),
        "product_master.csv": ("sku",), "transactions.csv": ("transaction_id",),
        "orders.csv": ("order_id",), "cycle_counts.csv": ("count_id",),
    }
    source_rows = {
        "inventory_snapshot.csv": snapshots, "product_master.csv": products_rows,
        "transactions.csv": transactions, "orders.csv": orders, "cycle_counts.csv": counts,
    }
    for filename, keys in required_keys.items():
        rows = source_rows[filename]
        nulls = sum(1 for row in rows for field in SOURCE_FIELDS[filename] if not row.get(field, "").strip())
        duplicates = len(rows) - len({tuple(row.get(key, "") for key in keys) for row in rows})
        affected = nulls + duplicates
        quality_rows.append({
            "check_name": f"{filename} required fields and duplicates",
            "status": "PASS" if affected == 0 else "FAIL", "records_affected": affected,
            "details": f"required fields present; unique key: {', '.join(keys)}",
        })
    transaction_types = {row["transaction_type"] for row in transactions}
    published_skus = [row["sku"] for row in stockout_rows]
    checks = [
        ("sku_reference_integrity", sum(row["sku"] not in products for row in snapshots + transactions + counts + orders), "all source SKUs exist in product master"),
        ("date_range_180_days", int(period_days != 180), f"observed period is {period_days} calendar days"),
        ("non_negative_inventory", sum(int(row["system_qty"]) < 0 or int(row["physical_qty"]) < 0 for row in snapshots), "system and physical quantities are non-negative"),
        ("snapshot_cost_matches_master", sum(round(float(row["unit_cost"]), 2) != round(float(products[row["sku"]]["unit_cost"]), 2) for row in snapshots), "snapshot unit costs match product master"),
        ("shipped_not_over_ordered", sum(int(row["shipped_qty"]) > int(row["ordered_qty"]) for row in orders), "shipped quantity does not exceed ordered quantity"),
        ("ship_date_not_before_order", sum(date.fromisoformat(row["ship_date"]) < date.fromisoformat(row["order_date"]) for row in orders), "shipment dates are not before order dates"),
        ("required_transaction_types", int(not {"RECEIPT", "PICK", "ADJUSTMENT", "TRANSFER_IN", "TRANSFER_OUT", "RETURN"}.issubset(transaction_types)), "all six documented movement types present"),
        ("partial_shipments", int(not any(int(row["shipped_qty"]) < int(row["ordered_qty"]) for row in orders)), "orders include partial shipments"),
        ("delayed_shipments", int(not any(date.fromisoformat(row["ship_date"]) > date.fromisoformat(row["promised_date"]) for row in orders)), "orders include delayed shipments"),
        ("minimum_order_volume", int(len(orders) < 3000), f"{len(orders)} orders"),
        ("minimum_transaction_volume", int(len(transactions) < 8000), f"{len(transactions)} transactions"),
        ("minimum_cycle_count_volume", int(len(counts) < 450), f"{len(counts)} counts"),
        ("replenishment_tier_reconciliation", int(sum(sku_tier_counts.values()) != len(replenishment_rows)), "Critical + High + Watch + Routine equals SKU rows"),
        ("replenishment_output_sku_grain", int(len(replenishment_rows) != len(products) or len({row["sku"] for row in replenishment_rows}) != len(replenishment_rows)), "one replenishment row per SKU"),
        ("count_tier_reconciliation", int(sum(count_tier_counts.values()) != len(count_rows)), "control tiers reconcile at SKU/location grain"),
        ("count_output_all_sku_locations", int(len(count_rows) != len(pair) or len(count_rows) != 3600), "all 3,600 SKU/location records retained"),
        ("replenishment_routine_majority", int(sku_tier_counts["Routine"] <= len(replenishment_rows) / 2), "Routine is the majority of SKU replenishment rows"),
        ("count_routine_majority", int(count_tier_counts["Routine"] <= len(count_rows) / 2), "Routine is the majority of SKU/location control rows"),
        ("stockout_report_sku_grain", int(len(published_skus) != len(set(published_skus))), "stockout report has one row per SKU"),
        ("stockout_report_tier_filter", sum(row["replenishment_tier"] not in {"Critical", "High"} or row["action_flag"] != "Y" for row in stockout_rows), "stockout report contains only Critical + High SKU rows"),
        ("count_queue_has_no_enterprise_stockout", int(any("stockout" in field.lower() or "replenishment" in field.lower() for field in COUNT_PRIORITY_FIELDS)), "count queue uses location-control signals and does not infer SKU stockout"),
    ]
    for check_name, affected, details in checks:
        quality_rows.append({
            "check_name": check_name, "status": "PASS" if affected == 0 else "FAIL",
            "records_affected": affected, "details": details,
        })

    write_csv("kpi_summary.csv", kpi_rows, KPI_FIELDS)
    write_csv("sku_replenishment_priorities.csv", replenishment_rows, REPLENISHMENT_FIELDS)
    write_csv("sku_location_count_priorities.csv", count_rows, COUNT_PRIORITY_FIELDS)
    write_csv("location_variance_summary.csv", location_rows, LOCATION_FIELDS)
    write_csv("stockout_risk_report.csv", stockout_rows, STOCKOUT_FIELDS)
    write_csv("data_quality_checks.csv", quality_rows, QUALITY_FIELDS)
    print(
        f"Analyzed {len(products)} SKUs, {len(snapshots):,} snapshots, "
        f"{len(transactions):,} transactions, {len(orders):,} orders, and "
        f"{len(counts):,} cycle counts. Replenishment tiers: "
        f"{dict(sku_tier_counts)}; count tiers: {dict(count_tier_counts)}."
    )


if __name__ == "__main__":
    main()
