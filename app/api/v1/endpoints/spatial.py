from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.data_gulma import DataGulma
from app.models.hasil_cluster import HasilCluster
from app.models.zona_gulma import ZonaGulma
from app.services.spatial_service import SpatialService

router = APIRouter()

@router.get("/geojson")
def get_spatial_geojson(
    batch_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Mengembalikan data GeoJSON FeatureCollection lengkap:
    1. Points koordinat gulma berwarna per klaster
    2. Poligon Convex Hull batas zona
    3. Titik centroid
    """
    batch_filter = batch_id or "default"

    # Ambil hasil clustering
    cluster_records = (
        db.query(HasilCluster, DataGulma)
        .join(DataGulma, HasilCluster.id_gulma == DataGulma.id_gulma)
        .filter(HasilCluster.batch_id == batch_filter)
        .all()
    )

    if not cluster_records:
        raise HTTPException(
            status_code=404, 
            detail="Hasil clustering untuk batch ini belum tersedia. Jalankan clustering terlebih dahulu."
        )

    # Ambil zona summaries
    zona_records = db.query(ZonaGulma).filter(ZonaGulma.batch_id == batch_filter).all()
    summaries = []
    for z in zona_records:
        color = "#22C55E" if z.nama_zona == "Rendah" else ("#EAB308" if z.nama_zona == "Sedang" else "#EF4444")
        summaries.append({
            "cluster": z.cluster_num,
            "zone": z.nama_zona,
            "coverage": z.coverage,
            "points_count": sum(1 for c, _ in cluster_records if c.cluster == z.cluster_num),
            "color": color,
            "recommendation": z.rekomendasi
        })

    # Siapkan list points
    points_data = []
    centroids_map = {}
    for h, d in cluster_records:
        points_data.append({
            "id": d.id_gulma,
            "latitude": float(d.latitude),
            "longitude": float(d.longitude),
            "persentase_gulma": d.persentase_gulma,
            "cluster": h.cluster,
            "jarak": h.jarak
        })
        if h.cluster not in centroids_map:
            centroids_map[h.cluster] = [float(h.centroid_x), float(h.centroid_y)]

    sorted_centroids = [centroids_map[k] for k in sorted(centroids_map.keys())]

    geojson = SpatialService.generate_geojson(
        points=points_data,
        summaries=summaries,
        centroids=sorted_centroids
    )
    return geojson

@router.get("/zone-summary")
def get_zone_summary_table(
    batch_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Menyajikan data tabel zonasi sesuai Gambar 3.10 (Halaman Peta Zona Gulma):
    Zone ID, Coordinates Centroid, Density Index/Coverage, Action Required.
    """
    batch_filter = batch_id or "default"
    zonas = db.query(ZonaGulma).filter(ZonaGulma.batch_id == batch_filter).all()
    if not zonas:
        raise HTTPException(status_code=404, detail="Data zona belum ditemukan.")

    # Ambil koordinat centroid dari hasil_cluster
    results = []
    for z in zonas:
        first_c = db.query(HasilCluster).filter(
            HasilCluster.batch_id == batch_filter,
            HasilCluster.cluster == z.cluster_num
        ).first()

        coords = f"{float(first_c.centroid_x):.6f}, {float(first_c.centroid_y):.6f}" if first_c else "-"
        results.append({
            "zone_id": f"SEC-0{z.cluster_num}",
            "cluster_num": z.cluster_num,
            "zone_name": z.nama_zona,
            "centroid_coordinates": coords,
            "coverage_percentage": f"{z.coverage:.2f}%",
            "action_required": z.rekomendasi
        })

    return results
