"""Generate deterministic synthetic inventory operations data.

Run from the repository root with:
    python projects/inventory-accuracy-stockout-risk/generate_data.py
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260905
ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"


def write_csv(name: str, rows: list[dict], fields: list[str]) -> None:
    path = RAW / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rng = random.Random(SEED)
    RAW.mkdir(parents=True, exist_ok=True)
    locations = [("DC01", "East"), ("DC02", "Central"), ("DC03", "West"), ("DC04", "South")]
    categories = ["Beverage", "Snacks", "Household", "Personal Care", "Pantry", "Pet"]
    products = []
    for i in range(1, 25):
        category = categories[(i - 1) % len(categories)]
        products.append(
            {
                "sku": f"SKU{i:03d}",
                "product_name": f"{category} Item {i:02d}",
                "category": category,
                "unit_cost": f"{rng.uniform(2.5, 48):.2f}",
                "reorder_point": rng.randint(8, 35),
                "target_stock_days": rng.randint(12, 28),
                "supplier_id": f"SUP{(i - 1) % 8 + 1:02d}",
            }
        )
    suppliers = [
        {"supplier_id": f"SUP{i:02d}", "supplier_name": f"Supplier {i:02d}",
         "promised_lead_days": rng.randint(3, 12)}
        for i in range(1, 9)
    ]
    write_csv("products.csv", products, list(products[0]))
    write_csv("locations.csv", [{"location_id": x, "region": y} for x, y in locations],
              ["location_id", "region"])
    write_csv("suppliers.csv", suppliers, list(suppliers[0]))

    start, end = date(2024, 1, 1), date(2025, 12, 31)
    inventory, sales, receipts, counts = [], [], [], []
    stock = {(p["sku"], loc[0]): rng.randint(25, 110) for p in products for loc in locations}
    demand = {p["sku"]: rng.uniform(0.35, 3.5) for p in products}
    for day_number in range((end - start).days + 1):
        current = start + timedelta(days=day_number)
        for p in products:
            for location_id, _ in locations:
                key = (p["sku"], location_id)
                opening = stock[key]
                # A few SKUs are deliberately fragile: high demand and unreliable supply.
                mean = demand[p["sku"]] * (1.35 if p["sku"] in {"SKU005", "SKU017", "SKU022"} else 1)
                sold = min(opening, max(0, int(rng.gauss(mean, max(0.4, mean * 0.35)))))
                receipt = 0
                if day_number > 0 and rng.random() < 0.035:
                    receipt = rng.randint(15, 75)
                    receipts.append({
                        "receipt_id": f"REC{len(receipts)+1:06d}", "receipt_date": current.isoformat(),
                        "sku": p["sku"], "location_id": location_id, "quantity_received": receipt,
                        "supplier_id": p["supplier_id"],
                    })
                closing = opening - sold + receipt
                stock[key] = closing
                sales.append({
                    "sale_date": current.isoformat(), "sku": p["sku"], "location_id": location_id,
                    "units_sold": sold,
                })
                # Physical counts happen monthly. Bias the counted quantity to create realistic variance.
                if current.day == 1:
                    count_error = rng.choice([0, 0, 0, -1, 1, 2, -2])
                    counts.append({
                        "count_id": f"CNT{len(counts)+1:06d}", "count_date": current.isoformat(),
                        "sku": p["sku"], "location_id": location_id,
                        "system_quantity": closing, "counted_quantity": max(0, closing + count_error),
                    })
                inventory.append({
                    "snapshot_date": current.isoformat(), "sku": p["sku"], "location_id": location_id,
                    "opening_quantity": opening, "units_sold": sold, "units_received": receipt,
                    "closing_quantity": closing,
                })
    write_csv("inventory_daily.csv", inventory, list(inventory[0]))
    write_csv("sales_daily.csv", sales, list(sales[0]))
    write_csv("receipts.csv", receipts, list(receipts[0]))
    write_csv("cycle_counts.csv", counts, list(counts[0]))
    print(f"Generated {len(inventory):,} inventory rows, {len(sales):,} sales rows, "
          f"{len(receipts):,} receipts, and {len(counts):,} cycle counts in {RAW}")


if __name__ == "__main__":
    main()
