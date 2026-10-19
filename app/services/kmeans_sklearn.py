import numpy as np
from sklearn.cluster import KMeans
from typing import List, Dict, Any, Tuple

class KMeansSklearn:
    def __init__(self, k: int = 3, max_iter: int = 300, tolerance: float = 1e-6, random_state: int = 42):
        self.k = k
        self.max_iter = max_iter
        self.tolerance = tolerance
        self.random_state = random_state

    def fit(self, points: List[Tuple[float, float]], initial_centroids: List[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Menjalankan K-Means menggunakan library scikit-learn.
        """
        n_samples = len(points)
        if n_samples < self.k:
            raise ValueError(f"Jumlah sampel ({n_samples}) tidak boleh lebih kecil dari K ({self.k})")

        X = np.array(points, dtype=np.float64)

        init_method = "k-means++"
        n_init = 10
        if initial_centroids and len(initial_centroids) == self.k:
            init_method = np.array(initial_centroids, dtype=np.float64)
            n_init = 1

        kmeans = KMeans(
            n_clusters=self.k,
            init=init_method,
            n_init=n_init,
            max_iter=self.max_iter,
            tol=self.tolerance,
            random_state=self.random_state
        )

        labels = kmeans.fit_predict(X)
        centroids = kmeans.cluster_centers_

        # Hitung jarak tiap titik ke centroid masing-masing
        distances = []
        for i in range(n_samples):
            c_pos = centroids[labels[i]]
            dist = float(np.linalg.norm(X[i] - c_pos))
            distances.append(dist)

        # Hitung Coverage per klaster (Persamaan 3.4) & Klasifikasi Zona (Proposal Bab 3.2.4 & Tabel 3.2)
        raw_summaries = []
        for c_idx in range(self.k):
            count = int(np.sum(labels == c_idx))
            coverage_pct = round((count / n_samples) * 100, 2)
            raw_summaries.append({
                "cluster": c_idx + 1,
                "centroid": {"latitude": float(centroids[c_idx][0]), "longitude": float(centroids[c_idx][1])},
                "points_count": count,
                "coverage": coverage_pct,
            })

        if self.k == 3:
            sorted_by_cov = sorted(raw_summaries, key=lambda x: x["coverage"])
            rank_meta = {
                0: ("Rendah", "#22C55E", "Routine Monitoring (Pengawasan rutin, perlakuan spot spraying minimal)"),
                1: ("Sedang", "#EAB308", "Targeted Control (Penyemprotan terarah dengan dosis sedang)"),
                2: ("Tinggi", "#EF4444", "Immediate Treatment (Penyemprotan intensif prioritas tinggi)")
            }
            cluster_summaries_map = {}
            for rank, item in enumerate(sorted_by_cov):
                z_name, color, recom = rank_meta[rank]
                cluster_summaries_map[item["cluster"]] = {
                    **item,
                    "zone": z_name,
                    "color": color,
                    "recommendation": recom
                }
            cluster_summaries = [cluster_summaries_map[c + 1] for c in range(self.k)]
        else:
            cluster_summaries = []
            for item in raw_summaries:
                cov = item["coverage"]
                if cov < 20.0:
                    z_name, color, recom = "Rendah", "#22C55E", "Routine Monitoring (Pengawasan rutin, perlakuan spot spraying minimal)"
                elif 20.0 <= cov <= 40.0:
                    z_name, color, recom = "Sedang", "#EAB308", "Targeted Control (Penyemprotan terarah dengan dosis sedang)"
                else:
                    z_name, color, recom = "Tinggi", "#EF4444", "Immediate Treatment (Penyemprotan intensif prioritas tinggi)"
                cluster_summaries.append({
                    **item,
                    "zone": z_name,
                    "color": color,
                    "recommendation": recom
                })

        return {
            "status": "success",
            "engine": "sklearn",
            "k": self.k,
            "total_points": n_samples,
            "iterations": int(kmeans.n_iter_),
            "centroids": centroids.tolist(),
            "assignments": labels.tolist(),
            "distances": distances,
            "summaries": cluster_summaries,
            "inertia": float(kmeans.inertia_)
        }
