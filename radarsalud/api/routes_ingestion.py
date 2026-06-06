"""Endpoints de ingesta (ejecución de conectores y carga de CSV)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from radarsalud.database import get_session
from radarsalud.services import ingestion_service

router = APIRouter(prefix="/api/v1", tags=["ingestion"])


class IngestRequest(BaseModel):
    source: str | None = None  # nombre de conector; None = todos


@router.post("/ingest/run")
def ingest_run(payload: IngestRequest, session: Session = Depends(get_session)):
    if payload.source:
        run = ingestion_service.run_source(session, payload.source)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Conector desconocido: {payload.source}")
        return {
            "source": payload.source,
            "status": run.status,
            "records_found": run.records_found,
            "records_inserted": run.records_inserted,
            "message": run.error_message,
        }
    runs = ingestion_service.run_all(session)
    return {
        "runs": [
            {
                "source_id": r.source_id,
                "status": r.status,
                "records_found": r.records_found,
                "records_inserted": r.records_inserted,
            }
            for r in runs
        ]
    }


@router.post("/uploads/csv")
async def upload_csv(
    file: UploadFile = File(...),
    source_name: str | None = Form(default=None),
    session: Session = Depends(get_session),
):
    """Importa un CSV real agregado como observaciones manual_import."""
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")
    result = ingestion_service.import_csv_content(session, content, source_name=source_name)
    if result["status"] == "rejected":
        raise HTTPException(status_code=422, detail=result)
    return result
