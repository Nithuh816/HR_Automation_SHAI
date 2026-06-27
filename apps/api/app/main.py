from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    applications,
    assessments,
    auth,
    candidate_portal,
    candidates,
    checklists,
    dashboard,
    departments,
    documents,
    health,
    interviews,
    lookups,
    offer_templates,
    offers,
    requisitions,
    rubrics,
    users,
)


def _configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(__import__("logging"), settings.log_level)
        ),
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _configure_logging()
    structlog.get_logger().info("api.startup", env=settings.app_env)
    yield
    structlog.get_logger().info("api.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="HR_Automation_SHAI API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(departments.router)
    app.include_router(requisitions.router)
    app.include_router(dashboard.router)
    app.include_router(lookups.router)
    app.include_router(candidates.router)
    app.include_router(applications.router)
    app.include_router(assessments.router)
    app.include_router(rubrics.router)
    app.include_router(interviews.router)
    app.include_router(offer_templates.router)
    app.include_router(offers.router)
    app.include_router(checklists.router)
    app.include_router(documents.router)
    app.include_router(candidate_portal.router)
    return app


app = create_app()
