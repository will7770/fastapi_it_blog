# test_connection.py
import asyncio
from sqlalchemy import text  # <-- Add this import
from src.database.core import engine

async def test_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))  # <-- Wrap in text()
        print("Connection successful:", result.fetchone())

asyncio.run(test_connection())