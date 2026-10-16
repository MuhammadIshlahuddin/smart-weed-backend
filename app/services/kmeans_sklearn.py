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

        # Hitung Coverage per klaster (Persamaan 3.4)
        cluster_summaries = []
        for c_idx in range(self.k):
            count = int(np.sum(labels == c_idx))
            coverage_pct = round((count / n_samples) * 100, 2)

            if coverage_pct < 20.0:
                zone_name = "Rendah"
                color = "#22C55E"
                recom = "Routine Monitoring (Pengawasan rutin, perlakuan spot spraying minimal)"
            elif 20.0 <= coverage_pct <= 40.0:
                zone_name = "Sedang"
                color = "#EAB308"
                recom = "Targeted Control (Penyemprotan terarah dengan dosis sedang)"
            else:
                zone_name = "Tinggi"
                color = "#EF4444"
                recom = "Immediate Treatment (Penyemprotan intensif prioritas tinggi)"

            cluster_summaries.append({
                "cluster": c_idx + 1,
                "centroid": {"latitude": float(centroids[c_idx][0]), "longitude": float(centroids[c_idx][1])},
                "points_count": count,
                "coverage": coverage_pct,
                "zone": zone_name,
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
