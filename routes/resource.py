# routes/resource.py: endpoint CRUD resource utama (motors)
from fastapi import APIRouter, HTTPException, Query, status

import database as db
from models import MotorCreate, MotorOut, MotorUpdate

router = APIRouter(prefix="/motors", tags=["Motors"])


@router.get("", response_model=list[MotorOut])
async def list_motors(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    # await melepas event loop selama menunggu I/O database (non-blocking)
    return await db.list_motors(skip, limit)


@router.get("/{motor_id}", response_model=MotorOut)
async def get_motor(motor_id: int):
    motor = await db.get_motor(motor_id)
    if not motor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Motor tidak dmotorukan")
    return motor


@router.post("", response_model=MotorOut, status_code=status.HTTP_201_CREATED)
async def create_motor(data: MotorCreate):
    new_id = await db.insert_motor(data.nama, data.merk, data.kategori, data.harga_sewa, data.stok)
    return await db.get_motor(new_id)


@router.put("/{motor_id}", response_model=MotorOut)
async def update_motor(motor_id: int, data: MotorUpdate):
    ok = await db.update_motor(motor_id, data.nama, data.merk, data.kategori, data.harga_sewa, data.stok)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Motor tidak dmotorukan")
    return await db.get_motor(motor_id)


@router.delete("/{motor_id}")
async def delete_motor(motor_id: int):
    ok = await db.delete_motor(motor_id)  # hard delete
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Motor tidak dmotorukan")
    return {"message": f"Motor {motor_id} dihapus permanen"}
