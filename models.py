# models.py: skema Pydantic untuk validasi request dan serialisasi response
from typing import Literal, Optional
from pydantic import BaseModel, Field


class MotorBase(BaseModel):
    nama: str = Field(..., min_length=1, max_length=100)   # mis. "Vario 160"
    merk: str = Field(..., min_length=1, max_length=50)    # mis. "Honda"
    kategori: str = Field(..., min_length=1, max_length=50)  # Matic / Sport / Bebek / Trail
    harga_sewa: float = Field(..., gt=0)  # per hari
    stok: int = Field(..., ge=0)          # unit tersedia


class MotorCreate(MotorBase):
    pass


class MotorUpdate(MotorBase):
    pass


class MotorOut(BaseModel):
    # Tanpa batas ge=0: respons harus bisa menampilkan stok apa adanya
    # (termasuk nilai minus saat demonstrasi race condition tanpa lock)
    id: int
    nama: str
    merk: str
    kategori: str
    harga_sewa: float
    stok: int

class TransactionCreate(BaseModel):
    motor_id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)


class TransactionOut(BaseModel):
    id: int
    motor_id: int
    qty: int
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: Optional[str] = None
