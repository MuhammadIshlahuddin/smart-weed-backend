import numpy as np
from scipy.spatial import ConvexHull
from typing import List, Dict, Any, Tuple

class SpatialService:
    @staticmethod
    def generate_geojson(
        points: List[Dict[str, Any]], 
        summaries: List[Dict[str, Any]],
        centroids: List[List[float]]
    ) -> Dict[str, Any]:
        """
        Menghasilkan GeoJSON FeatureCollection yang memuat:
        1. Layer titik gulma (Points)
        2. Layer poligon batas zona per klaster (Convex Hull Polygons)
        3. Layer pusat centroid (Centroid Points)
        """
        features = []

        # 1. Tambahkan titik-titik gulma
        for pt in points:
            cluster_id = pt.get("cluster", 1)
            # Dapatkan info zona berdasarkan cluster
            summary = next((s for s in summaries if s["cluster"] == cluster_id), None)
            zone_name = summary["zone"] if summary else "Rendah"
            color = summary["color"] if summary else "#22C55E"

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    # Format GeoJSON: [Longitude, Latitude]
                    "coordinates": [float(pt["longitude"]), float(pt["latitude"])]
                },
                "properties": {
                    "id": pt.get("id"),
                    "type": "weed_point",
                    "cluster": cluster_id,
                    "zone": zone_name,
                    "coverage_zone": zone_name,
                    "color": color,
                    "distance_to_centroid": pt.get("jarak", 0.0),
                    "weed_percentage": pt.get("persentase_gulma", 0.0)
                }
            })

        # 2. Tambahkan poligon Convex Hull untuk tiap klaster
        for summary in summaries:
            c_num = summary["cluster"]
            c_points = [
                [float(p["longitude"]), float(p["latitude"])] 
                for p in points if p.get("cluster") == c_num
            ]

            if len(c_points) >= 3:
                pts_arr = np.array(c_points)
                try:
                    hull = ConvexHull(pts_arr)
                    hull_coords = pts_arr[hull.vertices].tolist()
                    # Tutup poligon GeoJSON (titik pertama = titik terakhir)
                    hull_coords.append(hull_coords[0])

                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [hull_coords]
                        },
                        "properties": {
                            "type": "zone_polygon",
                            "cluster": c_num,
                            "zone": summary["zone"],
                            "coverage": summary["coverage"],
                            "points_count": summary["points_count"],
                            "color": summary["color"],
                            "recommendation": summary["recommendation"]
                        }
                    })
                except Exception:
                    pass

        # 3. Tambahkan titik Centroid
        for idx, c in enumerate(centroids):
            c_num = idx + 1
            summary = next((s for s in summaries if s["cluster"] == c_num), None)
            zone_name = summary["zone"] if summary else "Rendah"
            color = summary["color"] if summary else "#22C55E"

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    # Format GeoJSON: [Longitude, Latitude]
                    "coordinates": [float(c[1]), float(c[0])]
                },
                "properties": {
                    "type": "centroid",
                    "cluster": c_num,
                    "zone": zone_name,
                    "color": color,
                    "label": f"Centroid C{c_num}"
                }
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }
