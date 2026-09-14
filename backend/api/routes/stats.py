"""REST endpoints for aggregate statistics."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_stats_service
from api.schemas.stats import (
    CategoryStatsEntry,
    CollectionStatsEntry,
    DashboardStats,
    TimelineEntry,
    TimelinePeriod,
    ValuationStats,
)
from api.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    service: StatsService = Depends(get_stats_service),
) -> DashboardStats:
    """Top-level dashboard figures."""
    return await service.get_dashboard()


@router.get("/valuation", response_model=ValuationStats)
async def valuation(
    service: StatsService = Depends(get_stats_service),
) -> ValuationStats:
    """Aggregate valuation figures."""
    return await service.get_valuation()


@router.get("/collections", response_model=list[CollectionStatsEntry])
async def by_collection(
    service: StatsService = Depends(get_stats_service),
) -> list[CollectionStatsEntry]:
    """Per-collection breakdown."""
    return await service.get_by_collection()


@router.get("/categories", response_model=list[CategoryStatsEntry])
async def by_category(
    service: StatsService = Depends(get_stats_service),
) -> list[CategoryStatsEntry]:
    """Per-category breakdown."""
    return await service.get_by_category()


@router.get("/timeline", response_model=list[TimelineEntry])
async def timeline(
    period: TimelinePeriod = Query(TimelinePeriod.MONTH),
    service: StatsService = Depends(get_stats_service),
) -> list[TimelineEntry]:
    """Acquisition timeline grouped by month/quarter/year."""
    return await service.get_timeline(period)
