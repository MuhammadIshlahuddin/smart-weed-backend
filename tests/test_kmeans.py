import pytest
import math
from app.services.kmeans_scratch import KMeansScratch
from app.services.kmeans_sklearn import KMeansSklearn
from app.services.spatial_service import SpatialService
from app.services.timer_service import TimerService

def test_euclidean_distance_proposal_example():
    """
    Menguji perhitungan Euclidean distance sesuai contoh di Proposal Bab 3.2.6 Halaman 44:
    Titik Gulma B: (-7.513611, 112.691804)
    Centroid C1: (-7.513539, 112.691684)
    Hasil yang diharapkan: d = 0.000140
    """
    pointB = (-7.513611, 112.691804)
    centroidC1 = (-7.513539, 112.691684)
    dist = KMeansScratch.euclidean_distance(pointB, centroidC1)
    
    assert round(dist, 6) == 0.000140

def test_kmeans_scratch_convergence():
    points = [
        (-7.513542, 112.691583),
        (-7.513611, 112.691804),
        (-7.513633, 112.691969),
        (-7.513700, 112.692100),
        (-7.513800, 112.692200),
        (-7.513539, 112.691684),
    ]
    model = KMeansScratch(k=3, random_state=42)
    res = model.fit(points)

    assert res["status"] == "scratch" or res["engine"] == "scratch"
    assert len(res["centroids"]) == 3
    assert len(res["assignments"]) == len(points)
    
    # Total coverage harus 100%
    total_cov = sum(s["coverage"] for s in res["summaries"])
    assert round(total_cov, 1) == 100.0

def test_kmeans_sklearn_compatibility():
    points = [
        (-7.513542, 112.691583),
        (-7.513611, 112.691804),
        (-7.513633, 112.691969),
        (-7.513700, 112.692100),
        (-7.513800, 112.692200),
        (-7.513539, 112.691684),
    ]
    model = KMeansSklearn(k=3, random_state=42)
    res = model.fit(points)

    assert res["engine"] == "sklearn"
    assert len(res["centroids"]) == 3
    assert len(res["assignments"]) == len(points)

def test_spatial_geojson_generation():
    points_data = [
        {"id": 1, "latitude": -7.513542, "longitude": 112.691583, "cluster": 1, "jarak": 0.0001},
        {"id": 2, "latitude": -7.513611, "longitude": 112.691804, "cluster": 1, "jarak": 0.00012},
        {"id": 3, "latitude": -7.513633, "longitude": 112.691969, "cluster": 1, "jarak": 0.00008},
        {"id": 4, "latitude": -7.513700, "longitude": 112.692100, "cluster": 2, "jarak": 0.0002},
    ]
    summaries = [
        {"cluster": 1, "zone": "Rendah", "coverage": 75.0, "points_count": 3, "color": "#22C55E", "recommendation": "Routine"},
        {"cluster": 2, "zone": "Tinggi", "coverage": 25.0, "points_count": 1, "color": "#EF4444", "recommendation": "Immediate"},
    ]
    centroids = [[-7.5136, 112.6918], [-7.5137, 112.6921]]

    geojson = SpatialService.generate_geojson(points_data, summaries, centroids)

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0
    # Memastikan feature point dan poligon ada
    types = [f["properties"].get("type") for f in geojson["features"]]
    assert "weed_point" in types
    assert "zone_polygon" in types
    assert "centroid" in types
