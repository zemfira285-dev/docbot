import aiosqlite
from config import DB_PATH
from typing import Optional, List, Dict


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                iin TEXT UNIQUE,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                doc_type TEXT,
                amount REAL,
                product TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)
        await db.commit()


async def add_client(full_name: str, iin: str, phone: str = None, address: str = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT OR REPLACE INTO clients (full_name, iin, phone, address) VALUES (?, ?, ?, ?)",
            (full_name, iin, phone, address)
        )
        await db.commit()
        return cursor.lastrowid


async def get_client_by_iin(iin: str) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM clients WHERE iin = ?", (iin,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def search_clients(query: str) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM clients WHERE full_name LIKE ? OR iin LIKE ? ORDER BY full_name LIMIT 15",
            (f"%{query}%", f"%{query}%")
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_all_clients(limit: int = 50) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM clients ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def save_document(client_id: int, doc_type: str, amount: float, product: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO documents (client_id, doc_type, amount, product) VALUES (?, ?, ?, ?)",
            (client_id, doc_type, amount, product)
        )
        await db.commit()