"""Run this script once to generate data/sales_data.xlsx"""
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

PRODUCTS = [
    ("Laptop Pro 15", "Electronics"),
    ("Wireless Mouse", "Electronics"),
    ("USB-C Hub", "Electronics"),
    ("Standing Desk", "Furniture"),
    ("Ergonomic Chair", "Furniture"),
    ("Desk Lamp", "Furniture"),
    ("Notebook A4", "Stationery"),
    ("Ballpoint Pen Set", "Stationery"),
    ("Whiteboard", "Stationery"),
    ("Coffee Maker", "Appliances"),
    ("Water Filter", "Appliances"),
    ("Air Purifier", "Appliances"),
]

REGIONS = ["North", "South", "East", "West", "Central"]
SALESPEOPLE = ["Alice Johnson", "Bob Smith", "Carol White", "David Brown", "Eva Martinez"]
CUSTOMERS = [
    "Acme Corp", "Globex Inc", "Initech", "Umbrella Ltd", "Stark Industries",
    "Wayne Enterprises", "Oscorp", "LexCorp", "Cyberdyne", "Soylent Corp",
]
STATUSES = ["Completed", "Completed", "Completed", "Pending", "Cancelled"]

PRICES = {
    "Laptop Pro 15": 1299.00,
    "Wireless Mouse": 49.99,
    "USB-C Hub": 79.99,
    "Standing Desk": 499.00,
    "Ergonomic Chair": 389.00,
    "Desk Lamp": 59.99,
    "Notebook A4": 12.99,
    "Ballpoint Pen Set": 8.99,
    "Whiteboard": 149.99,
    "Coffee Maker": 89.99,
    "Water Filter": 129.00,
    "Air Purifier": 249.00,
}

start_date = date(2024, 1, 1)
rows = []
for i in range(1, 201):
    product, category = random.choice(PRODUCTS)
    quantity = random.randint(1, 20)
    unit_price = PRICES[product]
    total = round(quantity * unit_price, 2)
    order_date = start_date + timedelta(days=random.randint(0, 364))
    rows.append({
        "order_id": f"ORD-{i:04d}",
        "date": order_date,
        "product": product,
        "category": category,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_amount": total,
        "region": random.choice(REGIONS),
        "salesperson": random.choice(SALESPEOPLE),
        "customer": random.choice(CUSTOMERS),
        "status": random.choice(STATUSES),
    })

df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

Path("data").mkdir(exist_ok=True)
df.to_excel("data/sales_data.xlsx", index=False)
print(f"Created data/sales_data.xlsx with {len(df)} rows")
