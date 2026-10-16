from fastapi import APIRouter
from app.api.v1.endpoints import auth, weeds, clustering, spatial

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(weeds.router, prefix="/weeds", tags=["Weed Management"])
api_router.include_router(clustering.router, prefix="/clustering", tags=["Clustering Engine"])
api_router.include_router(spatial.router, prefix="/spatial", tags=["Spatial & GIS"])
