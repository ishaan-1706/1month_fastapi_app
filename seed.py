# seed.py

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import create_engine
from fastapi_postgres_app.models import Base, Item

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine & ensure tables exist
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

# Prepare a common UTC timestamp
now = datetime.now(timezone.utc)

# Build sample items with integer special_id
sample_items = []
for idx, (name, desc) in enumerate(
    [
        ("Widget", "A sample widget"),
        ("Gadget", "A fancy gadget"),
        ("Doodad", "Just a doodad"),
    ],
    start=1
):
    sample_items.append({
        "name": name,
        "description": desc,
        "available": True,
        "created_at": now,
        "email": f"{name.lower()}@example.com",
        "special_id": idx,           # integer matching your column type
    })

# Insert within a transaction
with engine.begin() as conn:
    conn.execute(Item.__table__.insert(), sample_items)

print(f"Inserted {len(sample_items)} items successfully.")
