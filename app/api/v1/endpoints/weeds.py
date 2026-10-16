import io
import uuid
from datetime import date, datetime
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.data_gulma import DataGulma
from app.schemas.weed_schema import WeedPointCreate, WeedPointResponse, DatasetUploadSummary

router = APIRouter()

@router.post("/upload-csv", response_model=DatasetUploadSummary, status_code=status.HTTP_201_CREATED)
async def upload_weed_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, 
            detail="Format file tidak didukung. Harap upload file berekstensi .csv atau .xlsx"
        )
    
    contents = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file: {str(e)}")

    # Validasi header/kolom yang dibutuhkan
    df.columns = [c.strip().lower() for c in df.columns]
    required_cols = {"latitude", "longitude"}
    if not required_cols.issubset(set(df.columns)):
        raise HTTPException(
            status_code=400, 
            detail="Kolom wajib 'latitude' dan 'longitude' tidak ditemukan pada dataset."
        )

    batch_id = str(uuid.uuid4())[:8]
    valid_records = 0
    invalid_records = 0

    records_to_insert = []
    today = date.today()

    for _, row in df.iterrows():
        try:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            
            # Validasi batasan geografis
            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                invalid_records += 1
                continue

            # Persentase tutupan gulma opsional / default
            pct = 0.0
            if "persentase_gulma" in row and not pd.isna(row["persentase_gulma"]):
                pct = float(row["persentase_gulma"])
            elif "persentase" in row and not pd.isna(row["persentase"]):
                pct = float(row["persentase"])

            # Tanggal observasi
            obs_date = today
            if "tanggal_observasi" in row and not pd.isna(row["tanggal_observasi"]):
                try:
                    obs_date = datetime.strptime(str(row["tanggal_observasi"]).strip(), "%Y-%m-%d").date()
                except Exception:
                    obs_date = today

            record = DataGulma(
                batch_id=batch_id,
                latitude=lat,
                longitude=lon,
                persentase_gulma=pct,
                tanggal_observasi=obs_date
            )
            records_to_insert.append(record)
            valid_records += 1
        except Exception:
            invalid_records += 1

    if not records_to_insert:
        raise HTTPException(status_code=400, detail="Tidak ada baris data valid yang dapat disimpan.")

    db.add_all(records_to_insert)
    db.commit()

    return {
        "batch_id": batch_id,
        "filename": file.filename,
        "total_records": len(df),
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "message": f"Dataset {file.filename} berhasil diunggah ({valid_records} titik valid)."
    }

@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    """
    Daftar inventaris dataset yang sudah diunggah ke sistem.
    """
    query = (
        db.query(
            DataGulma.batch_id,
            func.count(DataGulma.id_gulma).label("total_points"),
            func.min(DataGulma.tanggal_observasi).label("tanggal")
        )
        .group_by(DataGulma.batch_id)
        .all()
    )

    results = []
    for item in query:
        batch = item.batch_id if item.batch_id else "default"
        results.append({
            "batch_id": batch,
            "total_points": item.total_points,
            "tanggal": str(item.tanggal)
        })
    return results

@router.get("/points", response_model=List[WeedPointResponse])
def get_weed_points(
    batch_id: Optional[str] = Query(None),
    limit: int = 500,
    db: Session = Depends(get_db)
):
    query = db.query(DataGulma)
    if batch_id:
        query = query.filter(DataGulma.batch_id == batch_id)
    return query.limit(limit).all()

@router.post("/point", response_model=WeedPointResponse, status_code=status.HTTP_201_CREATED)
def create_single_weed_point(
    point_in: WeedPointCreate,
    batch_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    record = DataGulma(
        batch_id=batch_id or "manual",
        latitude=point_in.latitude,
        longitude=point_in.longitude,
        persentase_gulma=point_in.persentase_gulma,
        tanggal_observasi=point_in.tanggal_observasi or date.today()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
