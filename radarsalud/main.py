"""Aplicación FastAPI de RadarSalud: API REST + interfaz web Jinja2."""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from radarsalud import __version__
from radarsalud.api import (
    routes_alerts,
    routes_analytics,
    routes_dashboard,
    routes_ingestion,
    routes_maps,
    routes_observations,
    routes_simulation,
    routes_sources,
)
from radarsalud.database import get_session, init_db
from radarsalud.models import Alert, Observation, Simulation, Source
from radarsalud.services import map_service
from radarsalud.simulation.presets import list_presets
from radarsalud.utils.logging import configure_logging

WEB_DIR = Path(__file__).resolve().parent / "web"
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="RadarSalud",
        version=__version__,
        description=(
            "Vigilancia epidemiológica local con fuentes abiertas reales y modo "
            "simulación. No usa datos personales. No diagnostica. No sustituye a "
            "profesionales sanitarios."
        ),
    )

    # Estáticos
    static_dir = WEB_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Crea la base si no existe (no siembra catálogo; eso lo hace init-db).
    init_db()

    # Routers de la API
    app.include_router(routes_sources.router)
    app.include_router(routes_observations.router)
    app.include_router(routes_alerts.router)
    app.include_router(routes_maps.router)
    app.include_router(routes_analytics.router)
    app.include_router(routes_ingestion.router)
    app.include_router(routes_simulation.router)
    app.include_router(routes_dashboard.router)

    # --- Salud -------------------------------------------------------------
    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "service": "RadarSalud", "version": __version__}

    # --- Interfaz web ------------------------------------------------------
    @app.get("/", response_class=HTMLResponse, tags=["web"])
    def index(request: Request, session: Session = Depends(get_session)):
        counts = {
            "sources": session.scalar(select(func.count()).select_from(Source)) or 0,
            "observations_real": session.scalar(
                select(func.count()).select_from(Observation).where(
                    Observation.data_mode.in_(["real", "manual_import"])
                )
            ) or 0,
            "observations_sim": session.scalar(
                select(func.count()).select_from(Observation).where(
                    Observation.data_mode == "simulation"
                )
            ) or 0,
            "alerts_real": session.scalar(
                select(func.count()).select_from(Alert).where(Alert.data_mode == "real")
            ) or 0,
            "alerts_sim": session.scalar(
                select(func.count()).select_from(Alert).where(Alert.data_mode == "simulation")
            ) or 0,
            "simulations": session.scalar(select(func.count()).select_from(Simulation)) or 0,
        }
        return templates.TemplateResponse(
            request, "index.html", {"counts": counts, "version": __version__}
        )

    @app.get("/map", response_class=HTMLResponse, tags=["web"])
    def map_page(request: Request,
                 mode: str = Query(default="all", pattern="^(real|simulation|all)$")):
        return templates.TemplateResponse(request, "map.html", {"mode": mode})

    @app.get("/map/render", response_class=HTMLResponse, tags=["web"])
    def map_render(mode: str = Query(default="all", pattern="^(real|simulation|all)$"),
                   session: Session = Depends(get_session)):
        return HTMLResponse(map_service.render_map(session, mode))

    @app.get("/simulation", response_class=HTMLResponse, tags=["web"])
    def simulation_page(request: Request, session: Session = Depends(get_session)):
        sims = session.scalars(
            select(Simulation).order_by(Simulation.created_at.desc()).limit(20)
        ).all()
        return templates.TemplateResponse(
            request, "simulation.html", {"presets": list_presets(), "simulations": sims}
        )

    @app.get("/sources", response_class=HTMLResponse, tags=["web"])
    def sources_page(request: Request, session: Session = Depends(get_session)):
        sources = session.scalars(select(Source).order_by(Source.category, Source.name)).all()
        return templates.TemplateResponse(request, "sources.html", {"sources": sources})

    return app


app = create_app()
