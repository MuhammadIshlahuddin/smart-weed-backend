from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api.v1.api import api_router

# Inisialisasi skema tabel di database jika belum ada
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Backend RESTful API untuk Sistem Smart Weed Management berbasis K-Means Clustering "
        "dan Segmentasi Zona Spasial (Site-Specific Weed Management)."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Konfigurasi Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount folder static untuk Web Dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", tags=["Dashboard UI"])
    def serve_dashboard():
        return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy"}
