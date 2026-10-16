from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ClusteringExecuteRequest(BaseModel):
    batch_id: Optional[str] = None
    k: int = Field(default=3, ge=2, le=10, description="Jumlah cluster (K), default 3")
    engine: str = Field(default="scratch", description="Pilihan engine: 'scratch' atau 'sklearn'")
    max_iter: int = Field(default=300, ge=10, le=1000)
    tolerance: float = Field(default=1e-6)
    initial_centroids: Optional[List[List[float]]] = None

class CentroidPoint(BaseModel):
    latitude: float
    longitude: float

class ClusterSummary(BaseModel):
    cluster: int
    centroid: CentroidPoint
    points_count: int
    coverage: float
    zone: str
    color: str
    recommendation: str

class ClusteringExecuteResponse(BaseModel):
    status: str
    engine: str
    batch_id: Optional[str]
    total_points: int
    execution_time_ms: float
    iterations: int
    centroids: List[List[float]]
    summaries: List[ClusterSummary]
    iteration_logs: Optional[List[Dict[str, Any]]] = None

class BenchmarkRunResult(BaseModel):
    run_number: int
    scratch_time_ms: float
    sklearn_time_ms: float

class BenchmarkResponse(BaseModel):
    total_runs: int
    data_points: int
    k: int
    average_scratch_ms: float
    average_sklearn_ms: float
    runs: List[BenchmarkRunResult]
    conclusion: str
