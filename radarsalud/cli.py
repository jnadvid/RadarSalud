"""Interfaz de línea de comandos de RadarSalud (Typer)."""
from __future__ import annotations

from pathlib import Path

import typer
import uvicorn

from radarsalud.config import get_settings
from radarsalud.database import init_db, session_scope
from radarsalud.services import (
    analytics_service,
    ingestion_service,
    map_service,
    simulation_service,
    sources_service,
)
from radarsalud.utils.logging import configure_logging

app = typer.Typer(
    add_completion=False,
    help="RadarSalud · vigilancia epidemiológica local con datos abiertos y simulación.",
)


@app.command("init-db")
def init_db_cmd() -> None:
    """Crea la base SQLite y siembra el catálogo de fuentes."""
    configure_logging()
    init_db()
    with session_scope() as session:
        n = ingestion_service.seed_catalog(session)
    typer.echo(f"✅ Base inicializada y catálogo sembrado: {n} fuentes.")


@app.command("sources-list")
def sources_list() -> None:
    """Lista las fuentes catalogadas y su estado."""
    from sqlalchemy import select

    from radarsalud.models import Source

    with session_scope() as session:
        sources = session.scalars(select(Source).order_by(Source.category, Source.name)).all()
        if not sources:
            typer.echo("No hay fuentes. Ejecuta 'radarsalud init-db' primero.")
            raise typer.Exit()
        for s in sources:
            flag = "✓" if s.enabled else " "
            typer.echo(f"[{flag}] {s.name:32s} {s.category:14s} {s.access_mode}")


@app.command("sources-check")
def sources_check(
    include_datasets: bool = typer.Option(False, "--include-datasets"),
) -> None:
    """Comprueba todas las fuentes con URL y marca las que no responden."""
    configure_logging()
    with session_scope() as session:
        result = sources_service.check_all_sources(session, include_datasets=include_datasets)
    typer.echo(
        f"🔎 {result['checked']} comprobadas · 🟢 {result['reachable']} operativas · "
        f"🔴 {result['down']} caídas · ⚪ {result['not_checkable']} sin URL."
    )


@app.command("ingest")
def ingest(source: str = typer.Option(..., "--source", help="Nombre del conector/fuente")) -> None:
    """Ejecuta la ingesta de una fuente concreta."""
    configure_logging()
    with session_scope() as session:
        run = ingestion_service.run_source(session, source)
        if run is None:
            typer.echo(f"❌ Conector desconocido: {source}")
            raise typer.Exit(code=1)
        typer.echo(
            f"{source}: {run.status} · encontradas {run.records_found} · "
            f"insertadas {run.records_inserted}"
        )
        if run.error_message:
            typer.echo(f"   ↳ {run.error_message}")


@app.command("ingest-all")
def ingest_all() -> None:
    """Ejecuta la ingesta de todas las fuentes (operativas y plantillas)."""
    configure_logging()
    with session_scope() as session:
        runs = ingestion_service.run_all(session)
        # Leer atributos dentro del contexto de sesión (evita DetachedInstance).
        statuses = [r.status for r in runs]
    ok = sum(1 for s in statuses if s == "success")
    typer.echo(f"Ingesta completada: {len(statuses)} conectores, {ok} con datos reales.")


@app.command("import-csv")
def import_csv(
    file: Path = typer.Argument(..., exists=True, readable=True),
    mode: str = typer.Option("manual_import", "--mode", help="Etiqueta de modo (informativa)"),
    source_name: str | None = typer.Option(None, "--source-name"),
) -> None:
    """Importa un CSV real agregado como observaciones (manual_import)."""
    configure_logging()
    content = file.read_text(encoding="utf-8", errors="replace")
    with session_scope() as session:
        result = ingestion_service.import_csv_content(session, content, source_name=source_name)
    if result["status"] == "rejected":
        typer.echo(f"❌ CSV rechazado ({len(result['errors'])} errores):")
        for err in result["errors"][:20]:
            typer.echo(f"   - {err}")
        raise typer.Exit(code=1)
    typer.echo(f"✅ Importadas {result['inserted']} de {result['rows_total']} filas ({mode}).")


@app.command("analyze")
def analyze(
    mode: str = typer.Option("real", "--mode", help="real|simulation|all"),
    province: str | None = typer.Option(None, "--province"),
    event: str | None = typer.Option(None, "--event"),
) -> None:
    """Detecta anomalías y genera alertas según el modo de dato."""
    configure_logging()
    with session_scope() as session:
        try:
            summary = analytics_service.run_analysis(
                session, data_mode=mode, province=province, health_event=event
            )
        except ValueError as exc:
            typer.echo(f"❌ {exc}")
            raise typer.Exit(code=1) from exc
    typer.echo(f"✅ Análisis ({mode}): {summary['alerts_created']} alertas creadas.")
    for k, v in summary["by_mode"].items():
        typer.echo(f"   {k}: {v['observations']} obs · {v['alerts']} alertas")


@app.command("simulate")
def simulate(
    preset: str | None = typer.Option(None, "--preset", help="Nombre de escenario predefinido"),
    event: str = typer.Option("gripe", "--event"),
    province: str | None = typer.Option(None, "--province"),
    community: str | None = typer.Option(None, "--community"),
    severity: str = typer.Option("medium", "--severity"),
    days: int = typer.Option(14, "--days"),
    multiplier: float = typer.Option(2.5, "--multiplier"),
) -> None:
    """Lanza una simulación de brote (datos marcados como SIMULACIÓN)."""
    configure_logging()
    with session_scope() as session:
        try:
            if preset:
                result = simulation_service.run_preset(session, preset)
            else:
                result = simulation_service.run_simulation(
                    session, event=event, province=province, autonomous_community=community,
                    severity=severity, days=days, multiplier=multiplier,
                )
        except ValueError as exc:
            typer.echo(f"❌ {exc}")
            raise typer.Exit(code=1) from exc
    typer.echo(
        f"🧪 Simulación #{result['simulation_id']} creada: "
        f"{result['observations_created']} observaciones, "
        f"{result['alerts_created']} alertas (SIMULACIÓN)."
    )


@app.command("clear-simulations")
def clear_simulations() -> None:
    """Elimina todas las observaciones y alertas simuladas (no toca datos reales)."""
    configure_logging()
    with session_scope() as session:
        result = simulation_service.clear_simulations(session)
    typer.echo(
        f"🧹 Limpieza: {result['observations_deleted']} obs y "
        f"{result['alerts_deleted']} alertas simuladas eliminadas."
    )


@app.command("map")
def map_cmd(
    mode: str = typer.Option("all", "--mode", help="real|simulation|all"),
    output: Path | None = typer.Option(None, "--output", help="Ruta del HTML de salida"),
) -> None:
    """Genera el mapa de España en un fichero HTML."""
    configure_logging()
    settings = get_settings()
    settings.ensure_dirs()
    out = output or (settings.processed_dir / f"mapa_{mode}.html")
    with session_scope() as session:
        html = map_service.render_map(session, mode)
    out.write_text(html, encoding="utf-8")
    typer.echo(f"🗺️  Mapa ({mode}) generado en {out}")


@app.command("serve")
def serve(
    host: str | None = typer.Option(None, "--host"),
    port: int | None = typer.Option(None, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Arranca el servidor FastAPI local."""
    settings = get_settings()
    uvicorn.run(
        "radarsalud.main:app",
        host=host or settings.host,
        port=port or settings.port,
        reload=reload,
    )


if __name__ == "__main__":  # pragma: no cover
    app()
