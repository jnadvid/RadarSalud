"""Endpoints de simulación."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from radarsalud.database import get_session
from radarsalud.schemas.simulation import (
    ClearResult,
    SimulationRead,
    SimulationRequest,
)
from radarsalud.services import simulation_service

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


@router.post("/run")
def run_simulation(payload: SimulationRequest, session: Session = Depends(get_session)):
    result = simulation_service.run_simulation(
        session,
        event=payload.event,
        province=payload.province,
        autonomous_community=payload.autonomous_community,
        severity=payload.severity,
        days=payload.days,
        multiplier=payload.multiplier,
        name=payload.name,
        description=payload.description,
    )
    return result


@router.post("/preset/{preset_name}")
def run_preset(preset_name: str, session: Session = Depends(get_session)):
    try:
        return simulation_service.run_preset(session, preset_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/clear", response_model=ClearResult)
def clear_simulations(session: Session = Depends(get_session)):
    return simulation_service.clear_simulations(session)


@router.get("/list", response_model=list[SimulationRead])
def list_simulations(session: Session = Depends(get_session)):
    return simulation_service.list_simulations(session)
