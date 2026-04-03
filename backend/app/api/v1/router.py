"""API v1 router — aggregates all endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import analysis, auth, dashboard, labs, patients, records, reports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(records.router, prefix="/records", tags=["Medical Records"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["AI Analysis"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(labs.router, prefix="/labs", tags=["Lab Results"])
