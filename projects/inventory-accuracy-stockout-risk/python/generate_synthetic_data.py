"""Create fixed-seed synthetic inventory accuracy and stockout-risk source data."""
from __future__ import annotations
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260905
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def write(name, rows, fields):
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def main():
    rng = random.Random(SEED); DATA.mkdir(exist_ok=True)
    locations = ["DC01", "DC02", "DC03", "DC04"]
    products = []
    for i in range(1, 25):
        products.append({"sku": f"SKU{i:03d}", "product_name": f"Item {i:02d}",
            "category": ["Beverage","Snacks","Household","Pantry"][i % 4],
            "unit_cost": f"{rng.uniform(2, 48):.2f}", "reorder_point": rng.randint(8, 35),
            "lead_time_days": rng.randint(3, 12)})
    write("product_master.csv", products, list(products[0]))
    start, days = date(2024, 1, 1), 731
    stock = {(p["sku"], l): rng.randint(25, 110) for p in products for l in locations}
    snapshots, transactions, orders, counts = [], [], [], []
    for n in range(days):
        d = start + timedelta(n)
        for p in products:
            for l in locations:
                key = (p["sku"], l); opening = stock[key]
                avg = 1.2 + (int(p["sku"][-2:]) % 9) / 3
                sold = min(opening, max(0, int(rng.gauss(avg * (1.4 if p["sku"] in {"SKU005","SKU017","SKU022"} else 1), .7))))
                received = rng.randint(15, 75) if rng.random() < .035 else 0
                closing = opening - sold + received; stock[key] = closing
                snapshots.append({"snapshot_date": d.isoformat(), "sku": p["sku"], "location_id": l,
                    "opening_quantity": opening, "closing_quantity": closing})
                transactions.append({"transaction_date": d.isoformat(), "sku": p["sku"], "location_id": l,
                    "transaction_type": "SALE", "quantity": sold})
                if received:
                    transactions.append({"transaction_date": d.isoformat(), "sku": p["sku"], "location_id": l,
                        "transaction_type": "RECEIPT", "quantity": received})
                    orders.append({"order_id": f"ORD{len(orders)+1:06d}", "order_date": d.isoformat(),
                        "sku": p["sku"], "location_id": l, "quantity_ordered": received,
                        "quantity_received": received, "status": "RECEIVED"})
                if d.day == 1:
                    err = rng.choice([0, 0, 0, -1, 1, 2, -2])
                    counts.append({"count_id": f"CNT{len(counts)+1:06d}", "count_date": d.isoformat(),
                        "sku": p["sku"], "location_id": l, "system_quantity": closing,
                        "counted_quantity": max(0, closing + err)})
    write("inventory_snapshot.csv", snapshots, list(snapshots[0]))
    write("transactions.csv", transactions, list(transactions[0]))
    write("orders.csv", orders, list(orders[0]))
    write("cycle_counts.csv", counts, list(counts[0]))
    print(f"Generated {len(snapshots):,} snapshots and {len(transactions):,} transactions (seed {SEED}).")

if __name__ == "__main__":
    main()
