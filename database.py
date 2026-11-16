# database.py: koneksi aiosqlite, skema tabel, dan seluruh operasi DB (async / non-blocking)
import os
import aiosqlite

DB_PATH = os.getenv("DB_PATH", "rental.db")

# Catatan: kolom stok SENGAJA tanpa CHECK (stok >= 0) agar overselling pada
# Tahap 1 (tanpa lock) terlihat sebagai stok negatif. Proteksi stok dilakukan di aplikasi.
CREATE_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS motors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    merk TEXT NOT NULL,
    kategori TEXT NOT NULL,
    harga_sewa REAL NOT NULL,          -- harga sewa per hari
    stok INTEGER NOT NULL              -- jumlah unit motor tersedia
);
"""

CREATE_TRX_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    motor_id INTEGER NOT NULL,
    qty INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


async def _connect():
    # Satu koneksi per operasi: aman dipakai multi-worker (tiap proses punya koneksi sendiri).
    # timeout menunggu bila database sedang dikunci proses lain.
    db = await aiosqlite.connect(DB_PATH, timeout=30)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await _connect()
    try:
        await db.execute("PRAGMA journal_mode=WAL")  # baca/tulis lebih lancar antar worker
        await db.execute(CREATE_ITEMS_TABLE)
        await db.execute(CREATE_TRX_TABLE)
        await db.commit()
    finally:
        await db.close()


async def _fetch_all(sql, params=()):
    db = await _connect()
    try:
        cur = await db.execute(sql, params)
        return [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()


async def _fetch_one(sql, params=()):
    rows = await _fetch_all(sql, params)
    return rows[0] if rows else None


async def _execute(sql, params=()):
    """Jalankan INSERT/UPDATE/DELETE, kembalikan (lastrowid, rowcount)."""
    db = await _connect()
    try:
        cur = await db.execute(sql, params)
        await db.commit()
        return cur.lastrowid, cur.rowcount
    finally:
        await db.close()


# ---------- motors ----------
async def list_motors(skip: int, limit: int):
    return await _fetch_all("SELECT * FROM motors ORDER BY id LIMIT ? OFFSET ?", (limit, skip))


async def get_motor(motor_id: int):
    return await _fetch_one("SELECT * FROM motors WHERE id = ?", (motor_id,))


async def insert_motor(nama, merk, kategori, harga_sewa, stok):
    new_id, _ = await _execute(
        "INSERT INTO motors (nama, merk, kategori, harga_sewa, stok) VALUES (?, ?, ?, ?, ?)",
        (nama, merk, kategori, harga_sewa, stok),
    )
    return new_id


async def update_motor(motor_id, nama, merk, kategori, harga_sewa, stok):
    _, n = await _execute(
        "UPDATE motors SET nama=?, merk=?, kategori=?, harga_sewa=?, stok=? WHERE id=?",
        (nama, merk, kategori, harga_sewa, stok, motor_id),
    )
    return n > 0


async def delete_motor(motor_id):
    # Hard delete: baris dihapus permanen dari database
    _, n = await _execute("DELETE FROM motors WHERE id = ?", (motor_id,))
    return n > 0


# ---------- stok ----------
async def get_stok(motor_id: int) -> int:
    row = await _fetch_one("SELECT stok FROM motors WHERE id = ?", (motor_id,))
    return row["stok"] if row else 0


async def decrement_stok(motor_id: int, qty: int):
    """Pengurangan biasa (dipakai versi TANPA lock; bisa membuat stok negatif)."""
    await _execute("UPDATE motors SET stok = stok - ? WHERE id = ?", (qty, motor_id))


async def decrement_stok_atomic(motor_id: int, qty: int) -> bool:
    """Pengurangan atomik di level SQL: hanya berhasil bila stok masih cukup.
    Lapisan pengaman tambahan lintas-proses (multi-worker), karena asyncio.Lock
    hanya berlaku di dalam satu proses."""
    _, n = await _execute(
        "UPDATE motors SET stok = stok - ? WHERE id = ? AND stok >= ?", (qty, motor_id, qty)
    )
    return n > 0


async def increment_stok(motor_id: int, qty: int):
    await _execute("UPDATE motors SET stok = stok + ? WHERE id = ?", (qty, motor_id))


# ---------- transactions ----------
async def insert_transaction(motor_id: int, qty: int, status: str = "pending") -> int:
    new_id, _ = await _execute(
        "INSERT INTO transactions (motor_id, qty, status) VALUES (?, ?, ?)",
        (motor_id, qty, status),
    )
    return new_id


async def update_trx_status(trx_id: int, status: str):
    await _execute("UPDATE transactions SET status = ? WHERE id = ?", (status, trx_id))


async def get_transaction(trx_id: int):
    return await _fetch_one("SELECT * FROM transactions WHERE id = ?", (trx_id,))


async def list_transactions(status, skip: int, limit: int):
    if status:
        return await _fetch_all(
            "SELECT * FROM transactions WHERE status = ? ORDER BY id LIMIT ? OFFSET ?",
            (status, limit, skip),
        )
    return await _fetch_all("SELECT * FROM transactions ORDER BY id LIMIT ? OFFSET ?", (limit, skip))
