"""Build a small dimensional retail warehouse and dashboard dataset."""

from __future__ import annotations

import csv
import json
import random
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "orders.csv"
DB_PATH = ROOT / "data" / "warehouse" / "retailops.db"
DASHBOARD_DATA = ROOT / "dashboard" / "data.json"

PRODUCTS = [
    ("P101", "Wireless Headphones", "Electronics", 44.0, 89.0),
    ("P102", "Mechanical Keyboard", "Electronics", 51.0, 109.0),
    ("P103", "Travel Backpack", "Accessories", 28.0, 69.0),
    ("P104", "Insulated Bottle", "Accessories", 11.0, 32.0),
    ("P105", "Desk Lamp", "Home Office", 24.0, 58.0),
    ("P106", "Monitor Stand", "Home Office", 31.0, 74.0),
    ("P107", "Running Shoes", "Sports", 39.0, 95.0),
    ("P108", "Yoga Mat", "Sports", 17.0, 46.0),
]
REGIONS = ["North", "South", "East", "West"]
SEGMENTS = ["Consumer", "Corporate", "Small Business"]
CHANNELS = ["Direct", "Marketplace", "Partner"]


@dataclass(frozen=True)
class Order:
    order_id: str
    order_date: str
    promised_date: str
    delivered_date: str
    customer_id: str
    segment: str
    region: str
    channel: str
    product_id: str
    product_name: str
    category: str
    quantity: int
    unit_cost: float
    unit_price: float


def generate_orders(rows: int = 1800, seed: int = 42) -> list[Order]:
    rng = random.Random(seed)
    start = date(2025, 1, 1)
    orders: list[Order] = []
    for index in range(rows):
        order_day = start + timedelta(days=rng.randrange(365))
        promised = order_day + timedelta(days=rng.randint(3, 7))
        delivered = promised + timedelta(days=rng.choices([-2, -1, 0, 1, 2, 3], [8, 14, 45, 18, 10, 5])[0])
        product_id, name, category, base_cost, base_price = rng.choice(PRODUCTS)
        region = rng.choices(REGIONS, [28, 22, 30, 20])[0]
        segment = rng.choices(SEGMENTS, [58, 25, 17])[0]
        channel = rng.choices(CHANNELS, [48, 37, 15])[0]
        seasonal = 1.12 if order_day.month in (11, 12) else 1.0
        discount = rng.choices([1.0, 0.95, 0.90, 0.85], [55, 25, 15, 5])[0]
        orders.append(Order(
            order_id=f"ORD-{index + 1:06d}", order_date=order_day.isoformat(),
            promised_date=promised.isoformat(), delivered_date=delivered.isoformat(),
            customer_id=f"CUS-{rng.randint(1, 420):04d}", segment=segment, region=region,
            channel=channel, product_id=product_id, product_name=name, category=category,
            quantity=rng.randint(1, 5), unit_cost=round(base_cost * rng.uniform(.97, 1.04), 2),
            unit_price=round(base_price * seasonal * discount, 2),
        ))
    return orders


def validate(orders: list[Order]) -> None:
    ids = [row.order_id for row in orders]
    assert len(ids) == len(set(ids)), "duplicate order_id"
    assert all(row.quantity > 0 and row.unit_price >= 0 and row.unit_cost >= 0 for row in orders)
    assert all(row.region in REGIONS and row.channel in CHANNELS for row in orders)
    assert all(row.delivered_date >= row.order_date for row in orders)


def write_raw(orders: list[Order]) -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(Order.__annotations__))
        writer.writeheader()
        writer.writerows(row.__dict__ for row in orders)


def build_warehouse(orders: list[Order]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.unlink(missing_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE dim_date (
          date_key INTEGER PRIMARY KEY, full_date TEXT UNIQUE NOT NULL,
          year INTEGER NOT NULL, month INTEGER NOT NULL, month_name TEXT NOT NULL,
          quarter INTEGER NOT NULL
        );
        CREATE TABLE dim_product (
          product_key INTEGER PRIMARY KEY, product_id TEXT UNIQUE NOT NULL,
          product_name TEXT NOT NULL, category TEXT NOT NULL
        );
        CREATE TABLE dim_customer (
          customer_key INTEGER PRIMARY KEY, customer_id TEXT UNIQUE NOT NULL,
          segment TEXT NOT NULL, region TEXT NOT NULL
        );
        CREATE TABLE fact_orders (
          order_id TEXT PRIMARY KEY, date_key INTEGER NOT NULL, product_key INTEGER NOT NULL,
          customer_key INTEGER NOT NULL, channel TEXT NOT NULL, quantity INTEGER NOT NULL,
          revenue REAL NOT NULL, cost REAL NOT NULL, gross_profit REAL NOT NULL,
          on_time INTEGER NOT NULL,
          FOREIGN KEY(date_key) REFERENCES dim_date(date_key),
          FOREIGN KEY(product_key) REFERENCES dim_product(product_key),
          FOREIGN KEY(customer_key) REFERENCES dim_customer(customer_key)
        );
        """)
        unique_dates = sorted({row.order_date for row in orders})
        connection.executemany(
            "INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?)",
            [(int(d.replace("-", "")), d, date.fromisoformat(d).year, date.fromisoformat(d).month,
              date.fromisoformat(d).strftime("%b"), (date.fromisoformat(d).month - 1) // 3 + 1) for d in unique_dates],
        )
        unique_products = {row.product_id: (row.product_name, row.category) for row in orders}
        for key, (product_id, (name, category)) in enumerate(sorted(unique_products.items()), 1):
            connection.execute("INSERT INTO dim_product VALUES (?, ?, ?, ?)", (key, product_id, name, category))
        unique_customers = {row.customer_id: (row.segment, row.region) for row in orders}
        for key, (customer_id, (segment, region)) in enumerate(sorted(unique_customers.items()), 1):
            connection.execute("INSERT INTO dim_customer VALUES (?, ?, ?, ?)", (key, customer_id, segment, region))
        product_keys = dict(connection.execute("SELECT product_id, product_key FROM dim_product"))
        customer_keys = dict(connection.execute("SELECT customer_id, customer_key FROM dim_customer"))
        facts = []
        for row in orders:
            revenue = round(row.quantity * row.unit_price, 2)
            cost = round(row.quantity * row.unit_cost, 2)
            facts.append((row.order_id, int(row.order_date.replace("-", "")), product_keys[row.product_id],
                          customer_keys[row.customer_id], row.channel, row.quantity, revenue, cost,
                          round(revenue - cost, 2), int(row.delivered_date <= row.promised_date)))
        connection.executemany("INSERT INTO fact_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", facts)
        connection.executescript("""
        CREATE VIEW bi_order_performance AS
        SELECT
          d.full_date AS order_date,
          d.year,
          d.month,
          d.month_name,
          d.quarter,
          c.region,
          c.segment,
          p.category,
          p.product_name,
          f.channel,
          f.order_id,
          f.quantity,
          f.revenue,
          f.cost,
          f.gross_profit,
          ROUND(100.0 * f.gross_profit / NULLIF(f.revenue, 0), 1) AS gross_margin_pct,
          f.on_time
        FROM fact_orders f
        JOIN dim_date d ON d.date_key = f.date_key
        JOIN dim_product p ON p.product_key = f.product_key
        JOIN dim_customer c ON c.customer_key = f.customer_key;
        """)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        raw_revenue = round(sum(row.quantity * row.unit_price for row in orders), 2)
        warehouse_revenue = round(connection.execute("SELECT SUM(revenue) FROM fact_orders").fetchone()[0], 2)
        assert raw_revenue == warehouse_revenue, "revenue reconciliation failed"


def export_dashboard() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("""
          SELECT d.month, d.month_name, c.region, p.category, f.channel,
                 ROUND(SUM(f.revenue), 2) revenue,
                 ROUND(SUM(f.gross_profit), 2) profit,
                 COUNT(*) orders,
                 ROUND(100.0 * AVG(f.on_time), 1) on_time
          FROM fact_orders f
          JOIN dim_date d ON d.date_key = f.date_key
          JOIN dim_product p ON p.product_key = f.product_key
          JOIN dim_customer c ON c.customer_key = f.customer_key
          GROUP BY d.month, d.month_name, c.region, p.category, f.channel
          ORDER BY d.month, c.region, p.category, f.channel
        """).fetchall()
    payload = {"generated_at": date.today().isoformat(), "records": [dict(row) for row in rows]}
    DASHBOARD_DATA.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    orders = generate_orders()
    validate(orders)
    write_raw(orders)
    build_warehouse(orders)
    export_dashboard()
    print(f"Pipeline complete: {len(orders):,} orders → {DB_PATH.name} → {DASHBOARD_DATA.name}")


if __name__ == "__main__":
    main()
