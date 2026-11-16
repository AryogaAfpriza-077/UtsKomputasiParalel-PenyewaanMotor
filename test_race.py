# test_race.py: kirim 2 request transaksi serentak untuk motor dengan stok = 1
import asyncio

import httpx

BASE = "http://127.0.0.1:8000"


async def main():
    payload = {"motor_id": 1, "qty": 1}
    async with httpx.AsyncClient() as client:
        req1 = client.post(f"{BASE}/transactions", json=payload)
        req2 = client.post(f"{BASE}/transactions", json=payload)
        res1, res2 = await asyncio.gather(req1, req2)  # dikirim bersamaan

        print("Respon Request 1:", res1.status_code, res1.json())
        print("Respon Request 2:", res2.status_code, res2.json())

        motor = await client.get(f"{BASE}/motors/1")
        print("Stok akhir motor 1:", motor.json()["stok"])


if __name__ == "__main__":
    asyncio.run(main())
