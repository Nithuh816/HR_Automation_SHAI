"""Schemas for dashboards & reports (M10)."""

from __future__ import annotations

from pydantic import BaseModel


class ReportSummary(BaseModel):
    open_requisitions: int
    total_candidates: int
    active_applications: int
    offers_outstanding: int
    hires: int


class FunnelStage(BaseModel):
    stage: str
    label: str
    count: int


class FunnelReport(BaseModel):
    stages: list[FunnelStage]
    rejected: int
    total: int


class SourceCount(BaseModel):
    source: str
    label: str
    count: int


class DropOff(BaseModel):
    stage: str
    label: str
    count: int


class TimeToFillSample(BaseModel):
    requisition_id: int
    code: str
    title: str
    days: int


class TimeToFillReport(BaseModel):
    average_days: float | None
    samples: list[TimeToFillSample]


class RecruiterPerformance(BaseModel):
    recruiter_id: int
    recruiter_name: str
    candidates: int
    offers: int
    hires: int
