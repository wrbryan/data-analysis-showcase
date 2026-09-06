"""Generate deterministic synthetic inventory operations data."""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260905
START = date(2026, 1, 1)
DAYS = 180
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def write_csv(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    with (DATA / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rng = random.Random(SEED)
    DATA.mkdir(parents=True, exist_ok=True)
    categories = ["Industrial Supplies", "Electrical Components", "Safety Supplies",
                  "Packaging", "Tools", "Consumables", "Fasteners", "Maintenance Parts",
                  "Shipping Supplies", "Material Handling"]
    suppliers = ["Atlas Industrial", "Blue Ridge Supply", "Cedar Components",
                 "Harbor Safety", "Summit Packaging"]
    locations = [(f"Z{z}-B{b:02d}", f"Z{z}") for z in range(1, 4) for b in range(1, 5)]
    products = []
    for i in range(1, 301):
        cost = round(4 + ((i * 37) % 1200) / 10, 2)
        products.append({
            "sku": f"SKU{i:04d}", "product_name": f"{categories[i % 10]} {i:04d}",
            "category": categories[i % 10], "supplier": suppliers[i % 5],
            "unit_cost": f"{cost:.2f}", "lead_time_days": 4 + (i * 7) % 18,
            "reorder_point": 20 + (i * 11) % 80, "safety_stock": 10 + (i * 5) % 40,
            "annual_demand_estimate": 1200 + (i * 83) % 9000, "active_flag": "Y",
        })
    write_csv("product_master.csv", list(products[0]), products)
    stock = {(p["sku"], loc): 35 + rng.randrange(100) for p in products for loc, _ in locations}
    snapshots, transactions, orders, counts = [], [], [], []
    order_id = transaction_id = count_id = 0
    for day_no in range(DAYS):
        current = START + timedelta(days=day_no)
        for p_no, product in enumerate(products, 1):
            for loc_no, (location, zone) in enumerate(locations, 1):
                key = (product["sku"], location)
                opening = stock[key]
                demand = 2 + (p_no * 13 + loc_no) % 8 + (5 if p_no in (7, 44, 121, 208, 277) else 0)
                picked = min(opening, max(0, int(rng.gauss(demand, 1.5))))
                received = 0
                if (day_no + p_no * 3 + loc_no) % 17 == 0:
                    received = 35 + (p_no * 7 + loc_no) % 70
                stock[key] = opening - picked + received
                discrepancy = 0
                if (day_no * 19 + p_no * 7 + loc_no * 3) % 43 == 0:
                    discrepancy = (p_no + loc_no) % 5 - 2
                snapshots.append({"snapshot_date": current, "sku": product["sku"],
                    "location": location, "zone": zone, "system_qty": stock[key],
                    "physical_qty": max(0, stock[key] + discrepancy), "unit_cost": product["unit_cost"]})
                shift = ("Day", "Evening", "Night")[(day_no + loc_no) % 3]
                for kind, qty in (("PICK", picked), ("RECEIPT", received)):
                    if qty:
                        transaction_id += 1
                        transactions.append({"transaction_id": f"TXN{transaction_id:08d}",
                            "transaction_date": current, "sku": product["sku"], "location": location,
                            "zone": zone, "transaction_type": kind, "quantity": qty, "shift": shift,
                            "reference_id": f"{'ORD' if kind == 'RECEIPT' else 'PICK'}{transaction_id:08d}"})
                if received:
                    order_id += 1
                    delayed = order_id % 11 == 0
                    orders.append({"order_id": f"ORD{order_id:07d}", "order_date": current,
                        "sku": product["sku"], "ordered_qty": received, "shipped_qty": max(0, received - (8 if delayed else 0)),
                        "promised_date": current + timedelta(days=int(product["lead_time_days"])),
                        "ship_date": current + timedelta(days=int(product["lead_time_days"]) + delayed),
                        "customer_segment": ("Commercial", "Maintenance", "Retail", "Government", "Internal")[order_id % 5]})
                if day_no % 14 == 0:
                    count_id += 1
                    error = (p_no * 5 + loc_no + day_no) % 9 - 4
                    counts.append({"count_id": f"CNT{count_id:07d}", "count_date": current,
                        "sku": product["sku"], "location": location, "zone": zone,
                        "scheduled_flag": "Y", "completed_flag": "N" if count_id % 17 == 0 else "Y",
                        "recount_flag": "Y" if abs(error) >= 3 else "N", "variance_qty": error,
                        "counter_team": f"Team-{1 + (p_no + loc_no) % 6}"})
    write_csv("inventory_snapshot.csv", ["snapshot_date", "sku", "location", "zone", "system_qty", "physical_qty", "unit_cost"], snapshots)
    write_csv("transactions.csv", ["transaction_id", "transaction_date", "sku", "location", "zone", "transaction_type", "quantity", "shift", "reference_id"], transactions)
    write_csv("orders.csv", ["order_id", "order_date", "sku", "ordered_qty", "shipped_qty", "promised_date", "ship_date", "customer_segment"], orders)
    write_csv("cycle_counts.csv", ["count_id", "count_date", "sku", "location", "zone", "scheduled_flag", "completed_flag", "recount_flag", "variance_qty", "counter_team"], counts)
    print(f"Generated {len(products)} SKUs, {len(snapshots):,} snapshots, {len(transactions):,} transactions, {len(orders):,} orders, and {len(counts):,} cycle counts (seed {SEED}).")


if __name__ == "__main__":
    main()
