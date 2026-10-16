import math
import random
from typing import List, Dict, Any, Tuple

class KMeansScratch:
    def __init__(self, k: int = 3, max_iter: int = 300, tolerance: float = 1e-6, random_state: int = None):
        self.k = k
        self.max_iter = max_iter
        self.tolerance = tolerance
        self.random_state = random_state
        self.centroids: List[Tuple[float, float]] = []
        self.iteration_logs: List[Dict[str, Any]] = []

    @staticmethod
    def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """
        Rumus Persamaan (3.1): d = sqrt((x1 - x2)^2 + (y1 - y2)^2)
        """
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return math.sqrt(dx * dx + dy * dy)

    def fit(self, points: List[Tuple[float, float]], initial_centroids: List[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Menjalankan proses clustering K-Means secara iteratif.
        """
        if self.random_state is not None:
            random.seed(self.random_state)

        n_samples = len(points)
        if n_samples < self.k:
            raise ValueError(f"Jumlah sampel ({n_samples}) tidak boleh lebih kecil dari K ({self.k})")

        # 1. Inisialisasi Centroid
        if initial_centroids and len(initial_centroids) == self.k:
            self.centroids = [tuple(c) for c in initial_centroids]
        else:
            self.centroids = [tuple(c) for c in random.sample(points, self.k)]

        self.iteration_logs = []
        assignments = [0] * n_samples
        distances = [0.0] * n_samples

        for iteration in range(self.max_iter):
            # 2. Penugasan data ke cluster terdekat berdasarkan Euclidean Distance
            clusters: Dict[int, List[int]] = {i: [] for i in range(self.k)}
            for idx, pt in enumerate(points):
                min_dist = float("inf")
                closest_cluster = 0
                for c_idx, c_pos in enumerate(self.centroids):
                    dist = self.euclidean_distance(pt, c_pos)
                    if dist < min_dist:
                        min_dist = dist
                        closest_cluster = c_idx
                assignments[idx] = closest_cluster
                distances[idx] = min_dist
                clusters[closest_cluster].append(idx)

            # Catat log iterasi
            self.iteration_logs.append({
                "iteration": iteration + 1,
                "centroids": [list(c) for c in self.centroids],
                "cluster_sizes": [len(clusters[i]) for i in range(self.k)]
            })

            # 3. Pembaruan Centroid (Persamaan 3.2 & 3.3)
            new_centroids = []
            max_shift = 0.0

            for c_idx in range(self.k):
                member_indices = clusters[c_idx]
                if member_indices:
                    avg_x = sum(points[i][0] for i in member_indices) / len(member_indices)
                    avg_y = sum(points[i][1] for i in member_indices) / len(member_indices)
                    new_c = (avg_x, avg_y)
                else:
                    new_c = self.centroids[c_idx]

                shift = self.euclidean_distance(self.centroids[c_idx], new_c)
                if shift > max_shift:
                    max_shift = shift
                new_centroids.append(new_c)

            # 4. Cek Konvergensi
            if max_shift < self.tolerance:
                self.centroids = new_centroids
                break

            self.centroids = new_centroids

        # 5. Penghitungan Coverage (Persamaan 3.4) & Klasifikasi Zona
        cluster_summaries = []
        for c_idx in range(self.k):
            count = len(clusters[c_idx])
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
                "centroid": {"latitude": self.centroids[c_idx][0], "longitude": self.centroids[c_idx][1]},
                "points_count": count,
                "coverage": coverage_pct,
                "zone": zone_name,
                "color": color,
                "recommendation": recom
            })

        return {
            "status": "success",
            "engine": "scratch",
            "k": self.k,
            "total_points": n_samples,
            "iterations": len(self.iteration_logs),
            "centroids": [list(c) for c in self.centroids],
            "assignments": assignments,
            "distances": distances,
            "summaries": cluster_summaries,
            "iteration_logs": self.iteration_logs
        }
