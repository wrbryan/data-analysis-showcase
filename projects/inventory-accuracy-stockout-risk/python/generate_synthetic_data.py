"""Generate deterministic source data for the inventory analysis case study."""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260905
START_DATE = date(2026, 1, 1)
PERIOD_DAYS = 180
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

PRODUCT_FIELDS = [
    "sku", "description", "category", "supplier", "lead_time_days",
    "reorder_point", "safety_stock", "unit_cost",
]
SNAPSHOT_FIELDS = [
    "snapshot_date", "sku", "location", "system_qty", "physical_qty", "unit_cost",
]
TRANSACTION_FIELDS = [
    "transaction_date", "sku", "transaction_type", "quantity", "shift", "location",
]
ORDER_FIELDS = [
    "order_id", "order_date", "sku", "ordered_qty", "shipped_qty",
    "promised_date", "ship_date",
]
COUNT_FIELDS = [
    "count_id", "count_date", "sku", "location", "counter", "variance_qty",
    "recount_flag",
]


def _writer(path: Path, fields: list[str]) -> tuple[object, csv.DictWriter]:
    handle = path.open("w", newline="", encoding="utf-8")
    return handle, csv.DictWriter(handle, fieldnames=fields)


def main() -> None:
    rng = random.Random(SEED)
    DATA.mkdir(parents=True, exist_ok=True)
    categories = [
        "Beverages", "Snacks", "Pantry", "Household", "Personal Care",
        "Pet Care", "Paper Goods", "Small Appliances", "Cleaning", "Seasonal",
    ]
    suppliers = ["Northstar", "Acme Supply", "Blue Ridge", "Summit Goods", "Harbor Wholesale"]
    locations = [
        (f"Z{zone}-B{bin_no:02d}", f"Z{zone}", f"B{bin_no:02d}")
        for zone in range(1, 4)
        for bin_no in range(1, 5)
    ]
    products: list[dict[str, object]] = []
    for number in range(1, 301):
        category = categories[(number - 1) % len(categories)]
        cost = round(3.5 + ((number * 17) % 950) / 10, 2)
        lead_time = 3 + (number * 7) % 15
        reorder = 18 + (number * 11) % 65
        safety = 8 + (number * 5) % 35
        products.append({
            "sku": f"SKU{number:04d}",
            "description": f"{category} Item {number:04d}",
            "category": category,
            "supplier": suppliers[(number - 1) % len(suppliers)],
            "lead_time_days": lead_time,
            "reorder_point": reorder,
            "safety_stock": safety,
            "unit_cost": f"{cost:.2f}",
        })

    product_handle, product_writer = _writer(DATA / "product_master.csv", PRODUCT_FIELDS)
    product_writer.writeheader()
    product_writer.writerows(products)
    product_handle.close()

    snapshot_handle, snapshot_writer = _writer(DATA / "inventory_snapshot.csv", SNAPSHOT_FIELDS)
    transaction_handle, transaction_writer = _writer(DATA / "transactions.csv", TRANSACTION_FIELDS)
    order_handle, order_writer = _writer(DATA / "orders.csv", ORDER_FIELDS)
    count_handle, count_writer = _writer(DATA / "cycle_counts.csv", COUNT_FIELDS)
    for writer in (snapshot_writer, transaction_writer, order_writer, count_writer):
        writer.writeheader()

    stock: dict[tuple[str, str], int] = {
        (str(product["sku"]), location[0]): 45 + rng.randrange(115)
        for product in products for location in locations
    }
    order_number = count_number = 0
    for day_number in range(PERIOD_DAYS):
        current = START_DATE + timedelta(days=day_number)
        date_text = current.isoformat()
        for product_number, product in enumerate(products, start=1):
            sku = str(product["sku"])
            cost = str(product["unit_cost"])
            for location_number, (location, _zone, _bin_name) in enumerate(locations, start=1):
                key = (sku, location)
                opening = stock[key]
                demand_rate = 1 + ((product_number * 13 + location_number) % 7)
                if product_number in (7, 44, 121, 208, 277):
                    demand_rate += 5
                sold = min(opening, max(0, int(rng.gauss(demand_rate, 1.3))))
                receipt = 0
                if (day_number + product_number * 3 + location_number) % 17 == 0:
                    receipt = 35 + (product_number * 7 + location_number) % 70
                stock[key] = opening - sold + receipt
                transaction_writer.writerow({
                    "transaction_date": date_text, "sku": sku,
                    "transaction_type": "SALE", "quantity": sold,
                    "shift": ("A", "B", "C")[(day_number + location_number) % 3],
                    "location": location,
                })
                if receipt:
                    transaction_writer.writerow({
                        "transaction_date": date_text, "sku": sku,
                        "transaction_type": "RECEIPT", "quantity": receipt,
                        "shift": ("A", "B", "C")[(day_number + location_number) % 3],
                        "location": location,
                    })
                    order_number += 1
                    shipped = receipt if (order_number % 11) else max(0, receipt - 8)
                    promised = current + timedelta(days=int(product["lead_time_days"]))
                    ship_date = current + timedelta(days=int(product["lead_time_days"]) + (1 if order_number % 11 == 0 else 0))
                    order_writer.writerow({
                        "order_id": f"ORD{order_number:06d}",
                        "order_date": date_text,
                        "sku": sku,
                        "ordered_qty": receipt,
                        "shipped_qty": shipped,
                        "promised_date": promised.isoformat(),
                        "ship_date": ship_date.isoformat(),
                    })

                # A small, repeatable physical discrepancy creates realistic count work.
                discrepancy = 0
                if (day_number * 19 + product_number * 7 + location_number * 3) % 43 == 0:
                    discrepancy = ((product_number + location_number) % 5) - 2
                snapshot_writer.writerow({
                    "snapshot_date": date_text, "sku": sku, "location": location,
                    "system_qty": stock[key], "physical_qty": max(0, stock[key] + discrepancy),
                    "unit_cost": cost,
                })

                if day_number % 14 == 0:
                    count_number += 1
                    error = ((product_number * 5 + location_number + day_number) % 9) - 4
                    recount = abs(error) >= 3
                    count_writer.writerow({
                        "count_id": f"CNT{count_number:07d}",
                        "count_date": date_text,
                        "sku": sku,
                        "location": location,
                        "counter": f"Team-{1 + (product_number + location_number) % 6}",
                        "variance_qty": error,
                        "recount_flag": "Y" if recount else "N",
                    })

    for handle in (snapshot_handle, transaction_handle, order_handle, count_handle):
        handle.close()
    print(
        f"Generated 300 SKUs, {len(locations)} bins, {PERIOD_DAYS} days, "
        f"{order_number:,} orders, and {count_number:,} scheduled counts "
        f"(seed {SEED})."
    )


if __name__ == "__main__":
    main()
