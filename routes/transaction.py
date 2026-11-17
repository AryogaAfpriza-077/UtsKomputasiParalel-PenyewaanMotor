# routes/transaction.py: transaksi asinkron (BackgroundTasks) + pengamanan stok (asyncio.Lock)
import asyncio
import os
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

import database as db
from models import TransactionCreate, TransactionOut

router = APIRouter(prefix="/transactions", tags=["Transactions"])

# Gembok konkurensi tingkat modul. PENTING: asyncio.Lock hanya melindungi coroutine
# di dalam SATU proses/event loop. Pada --workers 4 setiap worker punya lock sendiri,
# sehingga untuk lintas-proses dipakai juga UPDATE atomik (decrement_stok_atomic).
stok_lock = asyncio.Lock()

# Mode pengujian B3: USE_LOCK=0 -> versi tanpa lock (demonstrasi race condition)
USE_LOCK = os.getenv("USE_LOCK", "1") == "1"


async def potong_stok_tanpa_lock(motor_id: int, qty: int) -> bool:
    """Versi 1 (RENTAN race condition): baca -> jeda -> tulis tanpa pengaman."""
    stok_terkini = await db.get_stok(motor_id)
    # Jeda buatan: saat coroutine ini menunggu, request lain ikut membaca stok yang sama
    await asyncio.sleep(0.01)
    if stok_terkini < qty:
        return False
    await db.decrement_stok(motor_id, qty)  # kedua request sama-sama mengurangi -> stok negatif
    return True


async def potong_stok_dengan_lock(motor_id: int, qty: int) -> bool:
    """Versi 2 (AMAN): critical section dilindungi asyncio.Lock."""
    # Hanya satu coroutine pada satu waktu yang boleh masuk blok ini;
    # coroutine lain menunggu di `async with` sampai lock dilepas.
    async with stok_lock:
        stok_terkini = await db.get_stok(motor_id)
        await asyncio.sleep(0.01)
        if stok_terkini < qty:
            return False
        # UPDATE atomik sebagai pengaman tambahan lintas-worker
        return await db.decrement_stok_atomic(motor_id, qty)


async def proses_transaksi_background(trx_id: int, motor_id: int, qty: int):
    """Fungsi pekerja internal (BUKAN endpoint HTTP) yang berjalan setelah respon terkirim."""
    try:
        await db.update_trx_status(trx_id, "processing")
        await asyncio.sleep(3)  # simulasi pekerjaan I/O intensif (non-blocking)
        await db.update_trx_status(trx_id, "completed")
    except Exception:
        # Bila gagal: tandai failed dan kembalikan stok yang sudah dipotong
        await db.update_trx_status(trx_id, "failed")
        await db.increment_stok(motor_id, qty)


@router.post("", response_model=TransactionOut, status_code=status.HTTP_202_ACCEPTED)
async def create_transaction(data: TransactionCreate, bg: BackgroundTasks):
    # 1. Validasi: resource harus terdaftar
    motor = await db.get_motor(data.motor_id)
    if not motor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Motor tidak ditemukan")

    # 2. Potong stok (dilindungi lock). Gagal -> 409 Conflict
    potong = potong_stok_dengan_lock if USE_LOCK else potong_stok_tanpa_lock
    if not await potong(data.motor_id, data.qty):
        raise HTTPException(status.HTTP_409_CONFLICT, "Unit motor habis atau tidak mencukupi")

    # 3. Simpan transaksi berstatus pending, lalu jadwalkan pemrosesan di latar belakang
    trx_id = await db.insert_transaction(data.motor_id, data.qty, status="pending")
    bg.add_task(proses_transaksi_background, trx_id, data.motor_id, data.qty)

    # 4. Respon langsung dikirim tanpa menunggu background task selesai
    return await db.get_transaction(trx_id)


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(pending|processing|completed|failed)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return await db.list_transactions(status_filter, skip, limit)


@router.get("/{trx_id}", response_model=TransactionOut)
async def get_transaction(trx_id: int):
    trx = await db.get_transaction(trx_id)
    if not trx:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaksi tidak ditemukan")
    return trx
