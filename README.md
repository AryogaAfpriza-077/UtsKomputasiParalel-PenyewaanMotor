https://youtu.be/GANTI_DENGAN_TAUTAN_VIDEO_UNLISTED

# API Penyewaan Motor (UTS Komputasi Paralel dan Terdistribusi)

Nama: ........  NIM: ........

REST API berbasis FastAPI + SQLite (aiosqlite) dengan transaksi asinkron (BackgroundTasks)
dan pengamanan stok memakai asyncio.Lock.

## Instalasi
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                   # isi 12 data motor
```

## Menjalankan
```bash
uvicorn main:app --port 8000                 # 1 worker
uvicorn main:app --workers 4 --port 8000     # 4 worker
```
Swagger UI: http://127.0.0.1:8000/docs

## Pengujian race condition (B3)
```bash
# Tahap 1: TANPA lock
python seed.py --stok 1 1
USE_LOCK=0 uvicorn main:app --port 8000      # Windows PowerShell: $env:USE_LOCK="0"; uvicorn main:app --port 8000
python test_race.py                          # terminal kedua: kedua sukses, stok akhir -1

# Tahap 2: DENGAN lock
python seed.py --stok 1 1
uvicorn main:app --port 8000                 # USE_LOCK default = 1
python test_race.py                          # satu sukses (202), satu 409 Conflict
```

## Benchmark Locust (C1)
Jalankan server (1 worker lalu 4 worker), lalu:
```bash
locust -f locustfile.py ReadUser  --headless -u 20 -r 20 --host http://127.0.0.1:8000 --csv hasil_read_1w
locust -f locustfile.py WriteUser --headless -u 10 -r 10 --host http://127.0.0.1:8000 --csv hasil_write_1w
```
Ulangi dengan `--workers 4` (ganti nama CSV, mis. `hasil_read_4w`).
Sebelum uji tulis: `python seed.py --reset && python seed.py --stok 2 1000` (agar stok motor id=2 tidak habis).

## Endpoint
| Method | Path | Keterangan |
|---|---|---|
| GET | /motors?skip=0&limit=10 | Daftar motor |
| GET | /motors/{id} | Detail motor |
| POST | /motors | Tambah motor (201) |
| PUT | /motors/{id} | Perbarui motor |
| DELETE | /motors/{id} | Hapus permanen |
| POST | /transactions | Buat transaksi (202, status pending; 409 bila stok habis) |
| GET | /transactions?status= | Daftar transaksi |
| GET | /transactions/{id} | Detail + status terkini |
