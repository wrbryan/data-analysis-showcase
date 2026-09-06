"""Analyze inventory accuracy and stockout risk using only the Python standard library."""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "outputs"


def read(name: str) -> list[dict]:
    with (RAW / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(name: str, rows: list[dict], fields: list[str]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    products = {r["sku"]: r for r in read("products.csv")}
    locations = {r["location_id"]: r for r in read("locations.csv")}
    inv, counts, sales = read("inventory_daily.csv"), read("cycle_counts.csv"), read("sales_daily.csv")
    accuracy = defaultdict(lambda: {"abs": 0.0, "count": 0, "bad": 0, "system": 0.0, "counted": 0.0})
    for r in counts:
        key = (r["sku"], r["location_id"])
        system, counted = int(r["system_quantity"]), int(r["counted_quantity"])
        accuracy[key]["abs"] += abs(system - counted)
        accuracy[key]["count"] += 1
        accuracy[key]["bad"] += abs(system - counted) > 1
        accuracy[key]["system"] += system
        accuracy[key]["counted"] += counted
    demand = defaultdict(list)
    for r in sales:
        demand[(r["sku"], r["location_id"])].append(int(r["units_sold"]))
    latest = {}
    zero_days = defaultdict(int)
    for r in inv:
        key = (r["sku"], r["location_id"])
        latest[key] = r
        zero_days[key] += int(int(r["closing_quantity"]) <= 0)
    risk_rows = []
    for key, last in latest.items():
        sku, loc = key
        daily = demand[key]
        avg = sum(daily) / len(daily)
        sd = math.sqrt(sum((x - avg) ** 2 for x in daily) / len(daily)) if daily else 0
        lead = 3 + (int(sku[-2:]) % 8)  # deterministic proxy consistent with supplier range
        current = int(last["closing_quantity"])
        safety = 1.65 * sd * math.sqrt(lead)
        reorder = float(products[sku]["reorder_point"])
        coverage = current / avg if avg else 999
        score = min(100, max(0, 100 * (
            0.55 * (zero_days[key] / len(daily))
            + 0.45 * max(0, (reorder + safety - current) / max(1, reorder + safety))
        )))
        risk = "High" if score >= 55 else "Medium" if score >= 25 else "Low"
        risk_rows.append({"sku": sku, "location_id": loc, "region": locations[loc]["region"],
                          "current_stock": current, "avg_daily_demand": f"{avg:.2f}",
                          "demand_stddev": f"{sd:.2f}", "lead_time_days": lead,
                          "safety_stock": f"{safety:.1f}", "days_of_cover": f"{coverage:.1f}",
                          "stockout_days": zero_days[key], "risk_score": f"{score:.1f}", "risk_band": risk})
    risk_rows.sort(key=lambda x: float(x["risk_score"]), reverse=True)
    write("stockout_risk_by_sku_location.csv", risk_rows, list(risk_rows[0]))
    acc_rows = []
    for (sku, loc), a in accuracy.items():
        acc_rows.append({"sku": sku, "location_id": loc, "region": locations[loc]["region"],
                         "count_events": a["count"], "absolute_variance_units": f"{a['abs']:.0f}",
                         "accuracy_pct": f"{max(0, 100 * (1 - a['abs'] / max(1, a['system']))):.2f}",
                         "variance_events_over_1_unit": a["bad"]})
    acc_rows.sort(key=lambda x: float(x["accuracy_pct"]))
    write("inventory_accuracy_by_sku_location.csv", acc_rows, list(acc_rows[0]))
    summary = {
        "seed": 20260905, "inventory_rows": len(inv), "cycle_count_events": len(counts),
        "overall_accuracy_pct": round(sum(float(x["accuracy_pct"]) for x in acc_rows) / len(acc_rows), 2),
        "high_risk_pairs": sum(x["risk_band"] == "High" for x in risk_rows),
        "medium_risk_pairs": sum(x["risk_band"] == "Medium" for x in risk_rows),
        "stockout_days_total": sum(zero_days.values()),
        "top_risk_pairs": [{"sku": x["sku"], "location_id": x["location_id"],
                            "risk_score": x["risk_score"]} for x in risk_rows[:10]],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
