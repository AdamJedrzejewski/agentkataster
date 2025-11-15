"""Main entry point for AgentKataster CLI."""
import asyncio
import sys
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import settings
from .database import init_db, SessionLocal
from .models import Municipality, ProcessingStatus, ScraperLog
from .worker import (
    scrape_municipality_parcels,
    scrape_municipality_plans,
    process_all_municipalities,
    init_municipalities
)

app = typer.Typer(
    name="agentkataster",
    help="Polish Land Registry Data Scraper - Collect parcel and spatial plan data"
)
console = Console()


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    logger.add(
        settings.log_file,
        rotation="10 MB",
        retention="30 days",
        level="DEBUG"
    )


@app.command()
def init():
    """Initialize the database and fetch all municipalities."""
    setup_logging()
    console.print("[bold green]Initializing AgentKataster...[/bold green]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating database...", total=None)

        # Create database tables
        init_db()
        progress.update(task, description="Database created ✓")

        # Fetch municipalities
        progress.update(task, description="Fetching municipalities from ULDK...")
        init_municipalities()
        progress.update(task, description="Municipalities initialized ✓")

    console.print("[bold green]✓ Initialization complete![/bold green]")


@app.command()
def status():
    """Show scraping status and statistics."""
    setup_logging()
    db = SessionLocal()

    try:
        # Get statistics
        total_municipalities = db.query(Municipality).count()

        parcels_completed = db.query(Municipality).filter(
            Municipality.parcels_status == ProcessingStatus.COMPLETED
        ).count()

        parcels_pending = db.query(Municipality).filter(
            Municipality.parcels_status == ProcessingStatus.PENDING
        ).count()

        parcels_failed = db.query(Municipality).filter(
            Municipality.parcels_status == ProcessingStatus.FAILED
        ).count()

        plans_completed = db.query(Municipality).filter(
            Municipality.plans_status == ProcessingStatus.COMPLETED
        ).count()

        plans_pending = db.query(Municipality).filter(
            Municipality.plans_status == ProcessingStatus.PENDING
        ).count()

        total_parcels = db.query(Municipality).with_entities(
            db.func.sum(Municipality.total_parcels)
        ).scalar() or 0

        # Create status table
        table = Table(title="AgentKataster Status", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Municipalities", str(total_municipalities))
        table.add_row("", "")
        table.add_row("[bold]Parcels Scraping[/bold]", "")
        table.add_row("  Completed", f"{parcels_completed} ({parcels_completed/total_municipalities*100:.1f}%)")
        table.add_row("  Pending", str(parcels_pending))
        table.add_row("  Failed", str(parcels_failed))
        table.add_row("", "")
        table.add_row("[bold]Plans Scraping[/bold]", "")
        table.add_row("  Completed", f"{plans_completed} ({plans_completed/total_municipalities*100:.1f}%)")
        table.add_row("  Pending", str(plans_pending))
        table.add_row("", "")
        table.add_row("[bold]Total Parcels Collected[/bold]", f"{total_parcels:,}")

        console.print(table)

        # Recent activity
        recent_logs = db.query(ScraperLog).order_by(
            ScraperLog.created_at.desc()
        ).limit(10).all()

        if recent_logs:
            console.print("\n[bold]Recent Activity:[/bold]")
            for log in recent_logs:
                status_emoji = "✓" if log.status == ProcessingStatus.COMPLETED else "✗"
                municipality = db.query(Municipality).get(log.municipality_id)
                muni_name = municipality.name if municipality else "Unknown"

                console.print(
                    f"  {status_emoji} {log.operation_type} - {muni_name} - "
                    f"{log.records_processed} records - "
                    f"{log.duration_seconds:.1f}s"
                )

    finally:
        db.close()


@app.command()
def start(
    no_parcels: bool = typer.Option(False, is_flag=True, help="Skip parcel data scraping"),
    no_plans: bool = typer.Option(False, is_flag=True, help="Skip spatial plans scraping"),
):
    """Start background scraping for all municipalities."""
    setup_logging()

    parcels = not no_parcels
    plans = not no_plans

    console.print("[bold green]Starting background scraping...[/bold green]")
    console.print(f"Scraping parcels: {parcels}")
    console.print(f"Scraping plans: {plans}")

    process_all_municipalities(scrape_parcels=parcels, scrape_plans=plans)

    console.print("[bold green]✓ Scraping jobs queued![/bold green]")
    console.print("Use 'agentkataster status' to monitor progress")


@app.command()
def scrape_municipality(
    teryt_code: str = typer.Argument(..., help="TERYT code of municipality"),
    no_parcels: bool = typer.Option(False, is_flag=True, help="Skip parcel data scraping"),
    no_plans: bool = typer.Option(False, is_flag=True, help="Skip spatial plans scraping"),
):
    """Scrape a specific municipality by TERYT code."""
    setup_logging()
    db = SessionLocal()

    parcels = not no_parcels
    plans = not no_plans

    try:
        municipality = db.query(Municipality).filter_by(code=teryt_code).first()

        if not municipality:
            console.print(f"[bold red]Municipality {teryt_code} not found![/bold red]")
            return

        console.print(f"[bold green]Scraping {municipality.name} ({teryt_code})[/bold green]")

        if parcels:
            console.print("Queuing parcel scraping...")
            scrape_municipality_parcels.delay(municipality.id)

        if plans:
            console.print("Queuing spatial plans scraping...")
            scrape_municipality_plans.delay(municipality.id)

        console.print("[bold green]✓ Jobs queued![/bold green]")

    finally:
        db.close()


@app.command()
def list_municipalities(
    limit: int = typer.Option(50, help="Number of municipalities to show"),
    pending_only: bool = typer.Option(False, is_flag=True, help="Show only pending municipalities"),
):
    """List municipalities in the database."""
    setup_logging()
    db = SessionLocal()

    try:
        query = db.query(Municipality)

        if pending_only:
            query = query.filter(
                (Municipality.parcels_status == ProcessingStatus.PENDING) |
                (Municipality.plans_status == ProcessingStatus.PENDING)
            )

        municipalities = query.limit(limit).all()

        table = Table(title="Municipalities", show_header=True)
        table.add_column("Code", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Type", style="yellow")
        table.add_column("Parcels", style="green")
        table.add_column("Plans", style="blue")

        for muni in municipalities:
            parcels_status = {
                ProcessingStatus.PENDING: "⏳",
                ProcessingStatus.IN_PROGRESS: "⚙️",
                ProcessingStatus.COMPLETED: "✓",
                ProcessingStatus.FAILED: "✗",
            }.get(muni.parcels_status, "?")

            plans_status = {
                ProcessingStatus.PENDING: "⏳",
                ProcessingStatus.IN_PROGRESS: "⚙️",
                ProcessingStatus.COMPLETED: "✓",
                ProcessingStatus.FAILED: "✗",
            }.get(muni.plans_status, "?")

            table.add_row(
                muni.code,
                muni.name,
                muni.type or "-",
                f"{parcels_status} ({muni.total_parcels:,})",
                plans_status,
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def export(
    output_file: str = typer.Argument(..., help="Output file path (GeoJSON or CSV)"),
    municipality_code: Optional[str] = typer.Option(None, help="Filter by municipality TERYT code"),
):
    """Export collected data to file."""
    setup_logging()
    console.print(f"[bold yellow]Export functionality coming soon![/bold yellow]")
    console.print(f"Will export to: {output_file}")


if __name__ == "__main__":
    app()
