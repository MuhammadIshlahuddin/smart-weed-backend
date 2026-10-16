from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from typing import Optional, List

class WeedPointCreate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Koordinat lintang [-90 s/d 90]")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Koordinat bujur [-180 s/d 180]")
    persentase_gulma: float = Field(..., ge=0.0, le=100.0, description="Persentase tutupan gulma [0 s/d 100%]")
    tanggal_observasi: Optional[date] = None

class WeedPointResponse(BaseModel):
    id_gulma: int
    batch_id: Optional[str]
    latitude: float
    longitude: float
    persentase_gulma: float
    tanggal_observasi: date
    model_config = ConfigDict(from_attributes=True)

class DatasetUploadSummary(BaseModel):
    batch_id: str
    filename: str
    total_records: int
    valid_records: int
    invalid_records: int
    message: str
