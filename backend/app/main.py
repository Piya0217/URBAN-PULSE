
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers.accidents import router as accidents_router
from backend.app.routers.violations import router as violations_router
from backend.app.routers.overview import router as overview_router
from backend.app.routers.insights import router as insights_router
from backend.app.routers.live_monitoring import router as live_monitoring_router
app = FastAPI(
    title="URBAN PULSE API",
    description="Bengaluru Urban Mobility and Road Safety Intelligence Platform",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "project": "URBAN PULSE",
    }


app.include_router(accidents_router)
app.include_router(violations_router)
app.include_router(overview_router)
app.include_router(insights_router)
app.include_router(live_monitoring_router)
