"""Celery worker for background processing."""
from datetime import datetime
from typing import Dict, Any

from celery import Celery
from celery.schedules import crontab
from loguru import logger

from .config import settings
from .database import SessionLocal, init_db
from .models import Municipality, ProcessingStatus, ScraperLog
from .scrapers import ULDKScraper, SpatialPlansScraper


# Initialize Celery
celery_app = Celery(
    'agentkataster',
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Warsaw',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
)


@celery_app.task(name='scrape_municipality_parcels')
def scrape_municipality_parcels(municipality_id: int) -> Dict[str, Any]:
    """
    Scrape parcels for a single municipality.

    Args:
        municipality_id: Database ID of municipality

    Returns:
        Statistics about the scraping operation
    """
    db = SessionLocal()
    started_at = datetime.utcnow()

    try:
        municipality = db.query(Municipality).get(municipality_id)
        if not municipality:
            logger.error(f"Municipality {municipality_id} not found")
            return {'status': 'failed', 'error': 'Municipality not found'}

        logger.info(
            f"Starting parcel scraping for {municipality.name} ({municipality.code})"
        )

        # Update status
        municipality.parcels_status = ProcessingStatus.IN_PROGRESS
        db.commit()

        # Create scraper and run
        import asyncio
        async def run_scraper():
            async with ULDKScraper() as scraper:
                return await scraper.scrape(
                    municipality.code,
                    municipality.name,
                    db
                )

        stats = asyncio.run(run_scraper())

        # Log the operation
        finished_at = datetime.utcnow()
        duration = (finished_at - started_at).total_seconds()

        log_entry = ScraperLog(
            municipality_id=municipality_id,
            operation_type='parcels',
            status=ProcessingStatus.COMPLETED if stats['status'] == 'completed' else ProcessingStatus.FAILED,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration,
            records_processed=stats.get('parcels_count', 0),
            error_message=stats.get('error'),
        )
        db.add(log_entry)
        db.commit()

        return stats

    except Exception as e:
        logger.error(f"Error in scrape_municipality_parcels: {e}")

        # Update municipality status
        municipality = db.query(Municipality).get(municipality_id)
        if municipality:
            municipality.parcels_status = ProcessingStatus.FAILED
            db.commit()

        # Log the failure
        log_entry = ScraperLog(
            municipality_id=municipality_id,
            operation_type='parcels',
            status=ProcessingStatus.FAILED,
            started_at=started_at,
            finished_at=datetime.utcnow(),
            duration_seconds=(datetime.utcnow() - started_at).total_seconds(),
            error_message=str(e),
        )
        db.add(log_entry)
        db.commit()

        return {'status': 'failed', 'error': str(e)}

    finally:
        db.close()


@celery_app.task(name='scrape_municipality_plans')
def scrape_municipality_plans(municipality_id: int) -> Dict[str, Any]:
    """
    Scrape spatial plans for a single municipality.

    Args:
        municipality_id: Database ID of municipality

    Returns:
        Statistics about the scraping operation
    """
    db = SessionLocal()
    started_at = datetime.utcnow()

    try:
        municipality = db.query(Municipality).get(municipality_id)
        if not municipality:
            logger.error(f"Municipality {municipality_id} not found")
            return {'status': 'failed', 'error': 'Municipality not found'}

        logger.info(
            f"Starting spatial plans scraping for {municipality.name} ({municipality.code})"
        )

        # Update status
        municipality.plans_status = ProcessingStatus.IN_PROGRESS
        db.commit()

        # Create scraper and run
        import asyncio
        async def run_scraper():
            async with SpatialPlansScraper() as scraper:
                return await scraper.scrape(
                    municipality.code,
                    municipality.name,
                    db
                )

        stats = asyncio.run(run_scraper())

        # Log the operation
        finished_at = datetime.utcnow()
        duration = (finished_at - started_at).total_seconds()

        log_entry = ScraperLog(
            municipality_id=municipality_id,
            operation_type='plans',
            status=ProcessingStatus.COMPLETED if stats['status'] == 'completed' else ProcessingStatus.FAILED,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration,
            records_processed=stats.get('mpzp_count', 0) + stats.get('suikzp_count', 0),
            error_message=stats.get('error'),
        )
        db.add(log_entry)
        db.commit()

        return stats

    except Exception as e:
        logger.error(f"Error in scrape_municipality_plans: {e}")

        # Update municipality status
        municipality = db.query(Municipality).get(municipality_id)
        if municipality:
            municipality.plans_status = ProcessingStatus.FAILED
            db.commit()

        # Log the failure
        log_entry = ScraperLog(
            municipality_id=municipality_id,
            operation_type='plans',
            status=ProcessingStatus.FAILED,
            started_at=started_at,
            finished_at=datetime.utcnow(),
            duration_seconds=(datetime.utcnow() - started_at).total_seconds(),
            error_message=str(e),
        )
        db.add(log_entry)
        db.commit()

        return {'status': 'failed', 'error': str(e)}

    finally:
        db.close()


@celery_app.task(name='process_all_municipalities')
def process_all_municipalities(scrape_parcels: bool = True, scrape_plans: bool = True):
    """
    Process all municipalities that haven't been scraped yet.

    This is the main background job that goes through municipalities one by one.

    Args:
        scrape_parcels: Whether to scrape parcel data
        scrape_plans: Whether to scrape spatial plans
    """
    db = SessionLocal()

    try:
        # Get municipalities that need processing
        query = db.query(Municipality)

        if scrape_parcels:
            pending_parcels = query.filter(
                Municipality.parcels_status.in_([
                    ProcessingStatus.PENDING,
                    ProcessingStatus.FAILED
                ])
            ).all()

            logger.info(f"Found {len(pending_parcels)} municipalities needing parcel data")

            for municipality in pending_parcels:
                logger.info(f"Queuing parcel scraping for {municipality.name}")
                scrape_municipality_parcels.delay(municipality.id)

        if scrape_plans:
            pending_plans = query.filter(
                Municipality.plans_status.in_([
                    ProcessingStatus.PENDING,
                    ProcessingStatus.FAILED
                ])
            ).all()

            logger.info(f"Found {len(pending_plans)} municipalities needing spatial plans")

            for municipality in pending_plans:
                logger.info(f"Queuing plans scraping for {municipality.name}")
                scrape_municipality_plans.delay(municipality.id)

    except Exception as e:
        logger.error(f"Error in process_all_municipalities: {e}")

    finally:
        db.close()


@celery_app.task(name='init_municipalities')
def init_municipalities():
    """
    Initialize the database with all Polish municipalities.

    This should be run once at the start to populate the municipalities table.
    """
    db = SessionLocal()

    try:
        logger.info("Initializing municipalities from ULDK...")

        import asyncio
        async def fetch_municipalities():
            async with ULDKScraper() as scraper:
                return await scraper.get_municipalities()

        municipalities_data = asyncio.run(fetch_municipalities())

        if not municipalities_data:
            logger.warning("No municipalities fetched")
            return

        # Save to database
        saved_count = 0
        for muni_data in municipalities_data:
            # Check if already exists
            existing = db.query(Municipality).filter_by(
                code=muni_data['code']
            ).first()

            if not existing:
                municipality = Municipality(
                    name=muni_data['name'],
                    code=muni_data['code'],
                    type=muni_data.get('type'),
                    county_id=None,  # TODO: Map to counties
                )
                db.add(municipality)
                saved_count += 1

                if saved_count % 100 == 0:
                    db.commit()
                    logger.info(f"Saved {saved_count} municipalities...")

        db.commit()
        logger.info(f"Successfully initialized {saved_count} municipalities")

    except Exception as e:
        logger.error(f"Error initializing municipalities: {e}")
        db.rollback()

    finally:
        db.close()


# Periodic tasks (optional - run automatically on schedule)
celery_app.conf.beat_schedule = {
    'process-municipalities-daily': {
        'task': 'process_all_municipalities',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
