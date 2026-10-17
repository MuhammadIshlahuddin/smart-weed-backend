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

import os

router = APIRouter()

@router.post("/load-sample", response_model=DatasetUploadSummary, status_code=status.HTTP_200_OK)
def load_sample_dataset(db: Session = Depends(get_db)):
    """
    Memuat dataset bawaan 225 titik koordinat sesuai proposal Bab 3.
    """
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "sample_weeds_225.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="File sample_weeds_225.csv tidak ditemukan di folder data/")

    df = pd.read_csv(csv_path)
    batch_id = "default"

    # Bersihkan batch_id lama jika ada
    db.query(DataGulma).filter(DataGulma.batch_id == batch_id).delete()

    records = []
    today = date.today()
    for _, row in df.iterrows():
        records.append(DataGulma(
            batch_id=batch_id,
            filename="sample_weeds_225.csv",
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            persentase_gulma=float(row["persentase_gulma"]),
            tanggal_observasi=today
        ))
    db.add_all(records)
    db.commit()

    return {
        "batch_id": batch_id,
        "filename": "sample_weeds_225.csv",
        "total_records": len(records),
        "valid_records": len(records),
        "invalid_records": 0,
        "message": f"Dataset proposal ({len(records)} titik gulma) berhasil dimuat ke sistem."
    }

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
        lower_name = file.filename.lower()
        if lower_name.endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(contents), sep=None, engine="python", encoding="utf-8-sig")
            except Exception:
                df = pd.read_csv(io.BytesIO(contents), encoding="latin1")
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
                filename=file.filename,
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
            func.max(DataGulma.filename).label("filename"),
            func.count(DataGulma.id_gulma).label("total_points"),
            func.max(DataGulma.tanggal_observasi).label("tanggal")
        )
        .group_by(DataGulma.batch_id)
        .order_by(DataGulma.id_gulma.desc())
        .all()
    )

    results = []
    for item in query:
        batch = item.batch_id if item.batch_id else "default"
        fname = item.filename or ("sample_weeds_225.csv" if item.total_points == 225 else "Data_Gulma.csv")
        results.append({
            "batch_id": batch,
            "filename": fname,
            "total_points": item.total_points,
            "tanggal": str(item.tanggal)
        })
    return results

@router.delete("/datasets/{batch_id}")
def delete_dataset(batch_id: str, db: Session = Depends(get_db)):
    """
    Menghapus satu dataset berdasarkan batch_id beserta hasil clustering dan zonasi terkait.
    """
    from app.models.hasil_cluster import HasilCluster
    from app.models.zona_gulma import ZonaGulma

    count = db.query(DataGulma).filter(DataGulma.batch_id == batch_id).count()
    if count == 0:
        raise HTTPException(status_code=404, detail="Dataset dengan ID tersebut tidak ditemukan.")

    db.query(HasilCluster).filter(HasilCluster.batch_id == batch_id).delete()
    db.query(ZonaGulma).filter(ZonaGulma.batch_id == batch_id).delete()
    db.query(DataGulma).filter(DataGulma.batch_id == batch_id).delete()
    db.commit()

    return {
        "status": "success",
        "message": f"Dataset #{batch_id} ({count} titik) berhasil dihapus."
    }

@router.delete("/datasets")
def clear_all_datasets(db: Session = Depends(get_db)):
    """
    Menghapus seluruh dataset dan hasil clustering dari sistem.
    """
    from app.models.hasil_cluster import HasilCluster
    from app.models.zona_gulma import ZonaGulma

    db.query(HasilCluster).delete()
    db.query(ZonaGulma).delete()
    deleted_count = db.query(DataGulma).delete()
    db.commit()

    return {
        "status": "success",
        "message": f"Seluruh dataset ({deleted_count} titik) berhasil dihapus."
    }

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
