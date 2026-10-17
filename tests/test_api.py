from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_full_pipeline_upload_and_clustering():
    # 1. Upload CSV dataset 225 titik
    with open("data/sample_weeds_225.csv", "rb") as f:
        upload_resp = client.post(
            "/api/v1/weeds/upload-csv",
            files={"file": ("sample_weeds_225.csv", f, "text/csv")}
        )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    batch_id = upload_data["batch_id"]
    assert upload_data["valid_records"] == 225

    # 2. Eksekusi K-Means Scratch Engine
    scratch_payload = {
        "batch_id": batch_id,
        "k": 3,
        "engine": "scratch",
        "max_iter": 300,
        "tolerance": 1e-6
    }
    cluster_resp = client.post("/api/v1/clustering/execute", json=scratch_payload)
    assert cluster_resp.status_code == 200
    cluster_data = cluster_resp.json()
    assert cluster_data["status"] == "success"
    assert cluster_data["engine"] == "scratch"
    assert cluster_data["total_points"] == 225
    assert len(cluster_data["centroids"]) == 3
    assert len(cluster_data["summaries"]) == 3
    assert cluster_data["execution_time_ms"] > 0

    # 3. Request GeoJSON hasil segmentasi
    spatial_resp = client.get(f"/api/v1/spatial/geojson?batch_id={batch_id}")
    assert spatial_resp.status_code == 200
    geo_data = spatial_resp.json()
    assert geo_data["type"] == "FeatureCollection"
    assert len(geo_data["features"]) > 225  # Memuat titik + poligon + centroid

    # 4. Request Ringkasan Tabel Zona
    summary_resp = client.get(f"/api/v1/spatial/zone-summary?batch_id={batch_id}")
    assert summary_resp.status_code == 200
    table_data = summary_resp.json()
    assert len(table_data) == 3

    # 5. Benchmark 5x ulangan (Bab 3.3.6)
    benchmark_resp = client.post(f"/api/v1/clustering/benchmark?batch_id={batch_id}&runs=5")
    assert benchmark_resp.status_code == 200
    bench_data = benchmark_resp.json()
    assert bench_data["total_runs"] == 5
    assert len(bench_data["runs"]) == 5
    assert bench_data["average_scratch_ms"] > 0
    assert bench_data["average_sklearn_ms"] > 0

    # 6. Test Delete Dataset
    delete_resp = client.delete(f"/api/v1/weeds/datasets/{batch_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "success"
