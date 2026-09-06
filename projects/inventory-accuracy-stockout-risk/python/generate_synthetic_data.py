"""Generate deterministic synthetic inventory operations data.

The population is intentionally shaped for two different operating queues:
SKU-level supply risk is concentrated in a small set of expensive, long-lead,
fast-moving products, while inventory-control exceptions are limited to a few
bins with recurring variance.  Full generated inputs are ignored by Git.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260905
START_DATE = date(2026, 1, 1)
DAYS = 180
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "generated"

PRODUCT_FIELDS = [
    "sku", "product_name", "category", "supplier", "unit_cost",
    "lead_time_days", "reorder_point", "safety_stock",
    "annual_demand_estimate", "active_flag",
]
SNAPSHOT_FIELDS = [
    "snapshot_date", "sku", "location", "zone", "system_qty",
    "physical_qty", "unit_cost",
]
TRANSACTION_FIELDS = [
    "transaction_id", "transaction_date", "sku", "location", "zone",
    "transaction_type", "quantity", "shift", "reference_id",
]
ORDER_FIELDS = [
    "order_id", "order_date", "sku", "ordered_qty", "shipped_qty",
    "promised_date", "ship_date", "customer_segment",
]
COUNT_FIELDS = [
    "count_id", "count_date", "sku", "location", "zone", "scheduled_flag",
    "completed_flag", "recount_flag", "variance_qty", "counter_team",
]


def write_csv(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    with (DATA / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rng = random.Random(SEED)
    DATA.mkdir(parents=True, exist_ok=True)

    categories = [
        "Industrial Supplies", "Electrical Components", "Safety Supplies",
        "Packaging", "Tools", "Consumables", "Fasteners", "Maintenance Parts",
        "Shipping Supplies", "Material Handling",
    ]
    suppliers = [
        "Atlas Industrial", "Blue Ridge Supply", "Cedar Components",
        "Harbor Safety", "Summit Packaging",
    ]
    locations = [
        (f"Z{zone}-B{bin_no:02d}", f"Z{zone}")
        for zone in range(1, 4)
        for bin_no in range(1, 5)
    ]
    # Seven products are deliberately exposed to enterprise supply risk.  The
    # risk is created through product attributes and demand/receipt behavior,
    # not by changing the analyzer's output tiers.
    critical_skus = {7, 44, 121, 208, 277}
    constrained_skus = {13, 188, 251}
    risk_skus = critical_skus | constrained_skus

    products: list[dict[str, object]] = []
    for number in range(1, 301):
        is_risk = number in risk_skus
        is_critical = number in critical_skus
        cost = (
            180 + ((number * 71) % 900) / 2
            if is_risk else 4 + ((number * 37) % 1200) / 10
        )
        lead_time = (
            28 + (number * 3) % 12
            if is_risk else 4 + (number * 7) % 18
        )
        demand_estimate = (
            18_000 + (number * 211) % 8_000
            if is_risk else 1_200 + (number * 83) % 9_000
        )
        products.append({
            "sku": f"SKU{number:04d}",
            "product_name": f"{categories[(number - 1) % len(categories)]} {number:04d}",
            "category": categories[(number - 1) % len(categories)],
            "supplier": suppliers[(number - 1) % len(suppliers)],
            "unit_cost": f"{cost:.2f}",
            "lead_time_days": lead_time,
            "reorder_point": (
                140 + (number * 7) % 80 if is_risk else 20 + (number * 11) % 80
            ),
            "safety_stock": (
                55 + (number * 3) % 30 if is_risk else 10 + (number * 5) % 40
            ),
            "annual_demand_estimate": demand_estimate,
            "active_flag": "Y",
        })
    write_csv("product_master.csv", PRODUCT_FIELDS, products)

    stock = {
        (product["sku"], location): (
            35 + rng.randrange(35) if int(product["sku"][3:]) in risk_skus
            else 80 + rng.randrange(70)
        )
        for product in products
        for location, _zone in locations
    }
    snapshots: list[dict[str, object]] = []
    transactions: list[dict[str, object]] = []
    orders: list[dict[str, object]] = []
    counts: list[dict[str, object]] = []
    transaction_number = order_number = count_number = 0
    variance_bins = {"Z2-B02", "Z3-B03"}

    def add_transaction(
        current: date, product: dict[str, object], location: str, zone: str,
        kind: str, quantity: int, shift: str, reference: str,
    ) -> None:
        nonlocal transaction_number
        if quantity <= 0:
            return
        transaction_number += 1
        transactions.append({
            "transaction_id": f"TXN{transaction_number:08d}",
            "transaction_date": current.isoformat(),
            "sku": product["sku"],
            "location": location,
            "zone": zone,
            "transaction_type": kind,
            "quantity": quantity,
            "shift": shift,
            "reference_id": reference,
        })

    for day_number in range(DAYS):
        current = START_DATE + timedelta(days=day_number)
        for product_number, product in enumerate(products, 1):
            sku = str(product["sku"])
            is_critical = product_number in critical_skus
            is_constrained = product_number in constrained_skus
            for location_number, (location, zone) in enumerate(locations, 1):
                key = (sku, location)
                opening = int(stock[key])
                if is_critical:
                    demand = 8 + (product_number + location_number) % 5
                elif is_constrained:
                    demand = 6 + (product_number + location_number) % 4
                else:
                    demand = 1 + (product_number * 13 + location_number) % 4
                picked = min(opening, max(0, int(rng.gauss(demand, 1.0))))
                received = 0
                # Healthy SKUs replenish regularly. Constrained SKUs replenish
                # infrequently; critical SKUs have no receipts in the period.
                if not is_critical and (
                    (day_number + product_number * 3 + location_number) % (
                        23 if is_constrained else 17
                    ) == 0
                ):
                    received = (
                        65 + (product_number * 7 + location_number) % 40
                        if is_constrained else 45 + (product_number * 7 + location_number) % 65
                    )
                stock[key] = opening - picked + received

                discrepancy = 0
                # Only two bins carry a recurring physical/system discrepancy.
                if location in variance_bins and (
                    day_number + product_number * 7 + location_number * 3
                ) % 43 == 0:
                    discrepancy = (product_number + location_number) % 5 - 2
                snapshots.append({
                    "snapshot_date": current.isoformat(),
                    "sku": sku,
                    "location": location,
                    "zone": zone,
                    "system_qty": stock[key],
                    "physical_qty": max(0, stock[key] + discrepancy),
                    "unit_cost": product["unit_cost"],
                })

                shift = ("Day", "Evening", "Night")[
                    (day_number + location_number) % 3
                ]
                add_transaction(
                    current, product, location, zone, "PICK", picked, shift,
                    f"PICK{transaction_number + 1:08d}",
                )
                add_transaction(
                    current, product, location, zone, "RECEIPT", received, shift,
                    f"RCV{transaction_number + 1:08d}",
                )

                # Orders are SKU-level customer demand: one line per SKU/day
                # rather than one duplicate order per warehouse location.
                if location_number == 1 and (day_number + product_number * 2) % 4 == 0:
                    order_number += 1
                    ordered = (
                        65 + (product_number * 5 + day_number) % 50
                        if is_critical else
                        45 + (product_number * 5 + day_number) % 35
                        if is_constrained else
                        8 + (product_number * 5 + day_number) % 28
                    )
                    partial = order_number % 7 == 0
                    delayed = order_number % 11 == 0
                    shipped = ordered - (8 if partial else 0)
                    promised = current + timedelta(days=int(product["lead_time_days"]))
                    ship_date = promised + timedelta(days=1 if delayed else 0)
                    orders.append({
                        "order_id": f"ORD{order_number:07d}",
                        "order_date": current.isoformat(),
                        "sku": sku,
                        "ordered_qty": ordered,
                        "shipped_qty": shipped,
                        "promised_date": promised.isoformat(),
                        "ship_date": ship_date.isoformat(),
                        "customer_segment": (
                            "Commercial", "Maintenance", "Retail",
                            "Government", "Internal",
                        )[order_number % 5],
                    })

                if (day_number + product_number + location_number) % 97 == 0:
                    add_transaction(
                        current, product, location, zone, "ADJUSTMENT",
                        1 + product_number % 3, shift,
                        f"ADJ{transaction_number + 1:08d}",
                    )
                if location_number < len(locations) and (
                    day_number + product_number
                ) % 113 == 0:
                    destination, destination_zone = locations[location_number]
                    transfer_qty = 2 + product_number % 4
                    add_transaction(
                        current, product, location, zone, "TRANSFER_OUT",
                        transfer_qty, shift, f"TRF{transaction_number + 1:08d}",
                    )
                    add_transaction(
                        current, product, destination, destination_zone,
                        "TRANSFER_IN", transfer_qty, shift,
                        f"TRF{transaction_number + 1:08d}",
                    )
                if (day_number + product_number * 3 + location_number) % 149 == 0:
                    add_transaction(
                        current, product, location, zone, "RETURN",
                        1 + product_number % 2, shift,
                        f"RET{transaction_number + 1:08d}",
                    )

                if day_number % 14 == 0:
                    count_number += 1
                    if location in variance_bins:
                        variance = (product_number * 5 + location_number + day_number) % 5 - 2
                    else:
                        variance = 0
                    completed = "N" if count_number % 17 == 0 else "Y"
                    # Recounts emerge from larger observed count variances;
                    # there is no output-rate target in the generator.
                    recount = "Y" if completed == "Y" and abs(variance) >= 1 else "N"
                    counts.append({
                        "count_id": f"CNT{count_number:07d}",
                        "count_date": current.isoformat(),
                        "sku": sku,
                        "location": location,
                        "zone": zone,
                        "scheduled_flag": "Y",
                        "completed_flag": completed,
                        "recount_flag": recount,
                        "variance_qty": variance,
                        "counter_team": f"Team-{1 + (product_number + location_number) % 6}",
                    })

    write_csv("inventory_snapshot.csv", SNAPSHOT_FIELDS, snapshots)
    write_csv("transactions.csv", TRANSACTION_FIELDS, transactions)
    write_csv("orders.csv", ORDER_FIELDS, orders)
    write_csv("cycle_counts.csv", COUNT_FIELDS, counts)
    print(
        f"Generated {len(products)} SKUs, {len(snapshots):,} snapshots, "
        f"{len(transactions):,} transactions, {len(orders):,} orders, and "
        f"{len(counts):,} cycle counts (seed {SEED})."
    )


if __name__ == "__main__":
    main()
