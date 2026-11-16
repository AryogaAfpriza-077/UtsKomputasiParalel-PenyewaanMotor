# seed.py: inisialisasi data awal (12 motor)
# Pemakaian:
#   python seed.py                 -> isi data bila tabel kosong
#   python seed.py --reset         -> hapus semua data lalu isi ulang
#   python seed.py --stok 1 1      -> set stok motor id=1 menjadi 1 (untuk test_race.py)
import asyncio
import sys

import aiosqlite

import database as db

DATA = [
    # (nama, merk, kategori, harga_sewa per hari, unit tersedia)
    ("Beat Street", "Honda", "Matic", 80000, 20),
    ("Vario 160", "Honda", "Matic", 100000, 15),
    ("Scoopy", "Honda", "Matic", 90000, 12),
    ("NMAX 155", "Yamaha", "Matic", 150000, 10),
    ("Mio M3", "Yamaha", "Matic", 75000, 18),
    ("Supra X 125", "Honda", "Bebek", 70000, 14),
    ("Revo", "Honda", "Bebek", 65000, 10),
    ("Vixion", "Yamaha", "Sport", 120000, 8),
    ("CBR 150R", "Honda", "Sport", 160000, 6),
    ("Ninja 250", "Kawasaki", "Sport", 250000, 4),
    ("KLX 150", "Kawasaki", "Trail", 180000, 5),
    ("CRF 150L", "Honda", "Trail", 175000, 5),
]


async def main():
    await db.init_db()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        if "--stok" in sys.argv:
            i = sys.argv.index("--stok")
            motor_id, stok = int(sys.argv[i + 1]), int(sys.argv[i + 2])
            await conn.execute("UPDATE motors SET stok=? WHERE id=?", (stok, motor_id))
            await conn.commit()
            print(f"Stok motor {motor_id} diset ke {stok}")
            return
        if "--reset" in sys.argv:
            await conn.execute("DELETE FROM transactions")
            await conn.execute("DELETE FROM motors")
            await conn.execute("DELETE FROM sqlite_sequence")
        cur = await conn.execute("SELECT COUNT(*) FROM motors")
        if (await cur.fetchone())[0] == 0:
            await conn.executemany(
                "INSERT INTO motors (nama, merk, kategori, harga_sewa, stok) VALUES (?, ?, ?, ?, ?)", DATA
            )
            await conn.commit()
            print(f"{len(DATA)} data berhasil dimasukkan")
        else:
            print("Tabel sudah berisi data (pakai --reset untuk mengulang)")


if __name__ == "__main__":
    asyncio.run(main())
