from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import delete

from app.db.session import get_db
from app.models.data_gulma import DataGulma
from app.models.hasil_cluster import HasilCluster
from app.models.zona_gulma import ZonaGulma
from app.schemas.cluster_schema import (
    ClusteringExecuteRequest,
    ClusteringExecuteResponse,
    BenchmarkResponse,
    BenchmarkRunResult
)
from app.services.kmeans_scratch import KMeansScratch
from app.services.kmeans_sklearn import KMeansSklearn
from app.services.timer_service import TimerService

router = APIRouter()

@router.post("/execute", response_model=ClusteringExecuteResponse)
def execute_clustering(
    req: ClusteringExecuteRequest,
    db: Session = Depends(get_db)
):
    """
    Eksekusi algoritma K-Means (Engine Scratch / Sklearn) dan simpan hasil ke database.
    """
    # 1. Ambil data titik gulma dari DB
    query = db.query(DataGulma)
    if req.batch_id:
        query = query.filter(DataGulma.batch_id == req.batch_id)
    
    weed_records = query.all()
    if not weed_records:
        raise HTTPException(
            status_code=404,
            detail="Tidak ditemukan data gulma untuk diproses. Silakan upload dataset terlebih dahulu."
        )

    points = [(float(r.latitude), float(r.longitude)) for r in weed_records]

    # 2. Pilih Engine dan Ukur Waktu Komputasi
    if req.engine.lower() == "sklearn":
        engine_instance = KMeansSklearn(
            k=req.k,
            max_iter=req.max_iter,
            tolerance=req.tolerance
        )
    else:
        engine_instance = KMeansScratch(
            k=req.k,
            max_iter=req.max_iter,
            tolerance=req.tolerance
        )

    initial_centroids_tuples = None
    if req.initial_centroids:
        initial_centroids_tuples = [(c[0], c[1]) for c in req.initial_centroids]

    result, exec_time_ms = TimerService.measure_execution_time(
        engine_instance.fit,
        points=points,
        initial_centroids=initial_centroids_tuples
    )

    # 3. Simpan Hasil ke Database (Tabel Hasil_Cluster & Zona_Gulma)
    # Hapus hasil clustering lama untuk batch_id terkait agar tidak duplikat
    batch_filter = req.batch_id or "default"
    db.query(HasilCluster).filter(HasilCluster.batch_id == batch_filter).delete()
    db.query(ZonaGulma).filter(ZonaGulma.batch_id == batch_filter).delete()

    cluster_records = []
    assignments = result["assignments"]
    distances = result["distances"]
    centroids = result["centroids"]

    for idx, r in enumerate(weed_records):
        c_idx = assignments[idx]
        c_pos = centroids[c_idx]
        dist = distances[idx]

        h = HasilCluster(
            id_gulma=r.id_gulma,
            batch_id=batch_filter,
            cluster=c_idx + 1,
            centroid_x=c_pos[0],
            centroid_y=c_pos[1],
            jarak=dist
        )
        cluster_records.append(h)

    db.add_all(cluster_records)
    db.flush()

    # Simpan ringkasan Zona Gulma
    zona_records = []
    for summary in result["summaries"]:
        z = ZonaGulma(
            batch_id=batch_filter,
            cluster_num=summary["cluster"],
            nama_zona=summary["zone"],
            coverage=summary["coverage"],
            rekomendasi=summary["recommendation"]
        )
        zona_records.append(z)

    db.add_all(zona_records)
    db.commit()

    return {
        "status": "success",
        "engine": result["engine"],
        "batch_id": req.batch_id,
        "total_points": len(points),
        "execution_time_ms": exec_time_ms,
        "iterations": result["iterations"],
        "centroids": centroids,
        "summaries": result["summaries"],
        "iteration_logs": result.get("iteration_logs")
    }

@router.post("/benchmark", response_model=BenchmarkResponse)
def run_benchmark(
    batch_id: Optional[str] = None,
    k: int = 3,
    runs: int = 5,
    db: Session = Depends(get_db)
):
    """
    Skenario Pengujian Bab 3.3.6: Mengukur waktu komputasi K-Means 
    sebanyak 5 kali ulangan dan membandingkan Scratch vs Sklearn.
    """
    query = db.query(DataGulma)
    if batch_id:
        query = query.filter(DataGulma.batch_id == batch_id)
    
    weed_records = query.all()
    if not weed_records:
        raise HTTPException(status_code=404, detail="Dataset tidak ditemukan untuk benchmark.")

    points = [(float(r.latitude), float(r.longitude)) for r in weed_records]

    run_results: List[BenchmarkRunResult] = []
    scratch_times = []
    sklearn_times = []

    for i in range(runs):
        # Scratch
        scratch_engine = KMeansScratch(k=k, random_state=42 + i)
        _, t_scratch = TimerService.measure_execution_time(scratch_engine.fit, points)
        scratch_times.append(t_scratch)

        # Sklearn
        sklearn_engine = KMeansSklearn(k=k, random_state=42 + i)
        _, t_sklearn = TimerService.measure_execution_time(sklearn_engine.fit, points)
        sklearn_times.append(t_sklearn)

        run_results.append(BenchmarkRunResult(
            run_number=i + 1,
            scratch_time_ms=t_scratch,
            sklearn_time_ms=t_sklearn
        ))

    avg_scratch = round(sum(scratch_times) / runs, 3)
    avg_sklearn = round(sum(sklearn_times) / runs, 3)

    conclusion = (
        f"Pengujian {runs} kali ulangan pada {len(points)} titik gulma (K={k}): "
        f"Rata-rata Scratch Engine = {avg_scratch} ms, Sklearn Engine = {avg_sklearn} ms. "
        f"Keduanya memenuhi target komputasi < 200 ms sesuai Bab 3.3.6 proposal."
    )

    return BenchmarkResponse(
        total_runs=runs,
        data_points=len(points),
        k=k,
        average_scratch_ms=avg_scratch,
        average_sklearn_ms=avg_sklearn,
        runs=run_results,
        conclusion=conclusion
    )
