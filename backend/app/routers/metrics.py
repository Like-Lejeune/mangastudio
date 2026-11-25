"""Indicateurs pour investisseurs : réservé à l'administration, lecture seule."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app import metrics
from app.db import get_session
from app.security import admin_user

router = APIRouter(prefix="/admin", tags=["indicateurs"], dependencies=[Depends(admin_user)])


@router.get("/metrics")
async def get_metrics(cohorts: int = Query(8, ge=1, le=26), session: AsyncSession = Depends(get_session)):
    return await metrics.compute(session, cohorts)


@router.get("/metrics.csv")
async def get_metrics_csv(session: AsyncSession = Depends(get_session)):
    data = await metrics.compute(session)
    return Response(metrics.monthly_csv(data), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="mangastudio-indicateurs.csv"'})
