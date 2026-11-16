# main.py: inisialisasi FastAPI dan registrasi router
from contextlib import asynccontextmanager

from fastapi import FastAPI

import database
from routes import resource, transaction


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()  # buat tabel bila belum ada (aman dijalankan tiap worker)
    yield


app = FastAPI(title="API Penyewaan Motor", version="1.0", lifespan=lifespan)
app.include_router(resource.router)
app.include_router(transaction.router)


@app.get("/", tags=["Root"])
async def root():
    return {"message": "API Penyewaan Motor", "docs": "/docs"}
