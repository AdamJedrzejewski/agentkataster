"""Scraper for spatial development plans (MPZP and SUiKZP)."""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from loguru import logger
from geopandas import GeoDataFrame
import geopandas as gpd
from shapely import wkt

from .base_scraper import BaseScraper
from ..models import Municipality, SpatialPlan, SpatialPlanType, ProcessingStatus


class SpatialPlansScraper(BaseScraper):
    """
    Scraper for spatial development plans.

    Collects:
    - MPZP (Miejscowy Plan Zagospodarowania Przestrzennego) - Local spatial development plans
    - SUiKZP (Studium Uwarunkowań i Kierunków Zagospodarowania Przestrzennego) - General plans
    """

    def __init__(self):
        super().__init__()
        # Multiple sources for spatial plans
        self.geoportal_wms_base = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/MPZP/WMS/SkorowidzeWMS"
        self.geoportal_wfs_base = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/MPZP/WFS/SkorowidzeWFS"

    async def get_plans_for_municipality(
        self,
        teryt_code: str,
        municipality_name: str,
        plan_type: SpatialPlanType = SpatialPlanType.MPZP
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get spatial development plans for a municipality.

        Args:
            teryt_code: TERYT code of municipality
            municipality_name: Name of municipality
            plan_type: Type of plan (MPZP or SUiKZP)

        Returns:
            List of plan dictionaries
        """
        logger.info(
            f"Fetching {plan_type.value.upper()} plans for "
            f"{municipality_name} ({teryt_code})"
        )

        # Try multiple data sources
        plans = []

        # 1. Try national geoportal
        geoportal_plans = await self._fetch_from_geoportal(
            teryt_code,
            plan_type
        )
        if geoportal_plans:
            plans.extend(geoportal_plans)

        # 2. Try local municipality geoportal (if exists)
        local_plans = await self._fetch_from_local_geoportal(
            teryt_code,
            municipality_name,
            plan_type
        )
        if local_plans:
            plans.extend(local_plans)

        # Deduplicate plans
        plans = self._deduplicate_plans(plans)

        logger.info(
            f"Found {len(plans)} {plan_type.value.upper()} plans "
            f"for {municipality_name}"
        )

        return plans if plans else None

    async def _fetch_from_geoportal(
        self,
        teryt_code: str,
        plan_type: SpatialPlanType
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch plans from national geoportal WFS."""
        try:
            # WFS GetFeature request
            params = {
                'SERVICE': 'WFS',
                'VERSION': '2.0.0',
                'REQUEST': 'GetFeature',
                'TYPENAME': 'ms:MPZP' if plan_type == SpatialPlanType.MPZP else 'ms:SUIKZP',
                'OUTPUTFORMAT': 'application/json',
                'CQL_FILTER': f"teryt='{teryt_code}'"
            }

            response = await self._make_request(
                self.geoportal_wfs_base,
                params=params
            )

            if not response:
                return None

            return self._parse_geojson_plans(response, plan_type)

        except Exception as e:
            logger.warning(f"Error fetching from geoportal: {e}")
            return None

    async def _fetch_from_local_geoportal(
        self,
        teryt_code: str,
        municipality_name: str,
        plan_type: SpatialPlanType
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch plans from local municipality geoportal.

        Many municipalities have their own geoportals with more detailed data.
        """
        # This would require a registry of municipality geoportals
        # For now, return None - this can be extended later
        logger.debug(f"Local geoportal lookup not yet implemented for {municipality_name}")
        return None

    def _parse_geojson_plans(
        self,
        geojson_data: Dict[str, Any],
        plan_type: SpatialPlanType
    ) -> List[Dict[str, Any]]:
        """Parse plans from GeoJSON response."""
        plans = []

        try:
            features = geojson_data.get('features', [])

            for feature in features:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry')

                plan = {
                    'plan_type': plan_type,
                    'name': properties.get('nazwa', properties.get('name', 'Unknown')),
                    'number': properties.get('numer_uchwaly', properties.get('number')),
                    'adoption_date': self._parse_date(properties.get('data_uchwalenia')),
                    'publication_date': self._parse_date(properties.get('data_publikacji')),
                    'effective_date': self._parse_date(properties.get('data_wejscia_w_zycie')),
                    'description': properties.get('opis'),
                    'zoning_code': properties.get('symbol_przeznaczenia'),
                    'zoning_description': properties.get('przeznaczenie'),
                    'building_conditions': properties.get('warunki_zabudowy'),
                    'document_url': properties.get('url_dokumentu'),
                    'wms_url': properties.get('wms_url'),
                    'wfs_url': properties.get('wfs_url'),
                    'geometry': geometry,
                    'data_source': 'Geoportal.gov.pl',
                    'is_valid': properties.get('aktualny', True),
                }

                plans.append(plan)

        except Exception as e:
            logger.error(f"Error parsing GeoJSON plans: {e}")

        return plans

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None

        # Try different date formats
        date_formats = [
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _deduplicate_plans(
        self,
        plans: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate plans based on name and number."""
        seen = set()
        unique_plans = []

        for plan in plans:
            # Create unique key from name and number
            key = (
                plan.get('name', '').lower(),
                plan.get('number', '').lower()
            )

            if key not in seen:
                seen.add(key)
                unique_plans.append(plan)

        return unique_plans

    async def scrape(
        self,
        municipality_code: str,
        municipality_name: str,
        db_session
    ) -> Dict[str, Any]:
        """
        Main scraping method for spatial plans.

        Args:
            municipality_code: TERYT code
            municipality_name: Municipality name
            db_session: Database session

        Returns:
            Statistics about the scraping operation
        """
        start_time = datetime.utcnow()
        stats = {
            'municipality_code': municipality_code,
            'municipality_name': municipality_name,
            'mpzp_count': 0,
            'suikzp_count': 0,
            'status': ProcessingStatus.IN_PROGRESS.value,
            'error': None
        }

        try:
            municipality = db_session.query(Municipality).filter_by(
                code=municipality_code
            ).first()

            if not municipality:
                logger.error(f"Municipality {municipality_code} not found in database")
                stats['status'] = ProcessingStatus.FAILED.value
                stats['error'] = "Municipality not found in database"
                return stats

            # Fetch MPZP plans
            mpzp_plans = await self.get_plans_for_municipality(
                municipality_code,
                municipality_name,
                SpatialPlanType.MPZP
            )

            if mpzp_plans:
                mpzp_saved = self._save_plans(mpzp_plans, municipality.id, db_session)
                stats['mpzp_count'] = mpzp_saved

            # Fetch SUiKZP plans
            suikzp_plans = await self.get_plans_for_municipality(
                municipality_code,
                municipality_name,
                SpatialPlanType.SUIKZP
            )

            if suikzp_plans:
                suikzp_saved = self._save_plans(suikzp_plans, municipality.id, db_session)
                stats['suikzp_count'] = suikzp_saved

            # Update municipality status
            municipality.plans_status = ProcessingStatus.COMPLETED
            municipality.plans_processed_at = datetime.utcnow()
            db_session.commit()

            stats['status'] = ProcessingStatus.COMPLETED.value

            logger.info(
                f"Successfully scraped {stats['mpzp_count']} MPZP and "
                f"{stats['suikzp_count']} SUiKZP plans for {municipality_name}"
            )

        except Exception as e:
            logger.error(f"Error scraping plans for {municipality_code}: {e}")
            stats['status'] = ProcessingStatus.FAILED.value
            stats['error'] = str(e)
            db_session.rollback()

        return stats

    def _save_plans(
        self,
        plans: List[Dict[str, Any]],
        municipality_id: int,
        db_session
    ) -> int:
        """Save plans to database."""
        saved_count = 0

        for plan_data in plans:
            try:
                # Convert geometry if present
                geometry_wkt = None
                if plan_data.get('geometry'):
                    from shapely.geometry import shape
                    geom = shape(plan_data['geometry'])
                    geometry_wkt = f"SRID=2180;{geom.wkt}"

                plan = SpatialPlan(
                    municipality_id=municipality_id,
                    plan_type=plan_data['plan_type'],
                    name=plan_data.get('name'),
                    number=plan_data.get('number'),
                    adoption_date=plan_data.get('adoption_date'),
                    publication_date=plan_data.get('publication_date'),
                    effective_date=plan_data.get('effective_date'),
                    description=plan_data.get('description'),
                    zoning_code=plan_data.get('zoning_code'),
                    zoning_description=plan_data.get('zoning_description'),
                    building_conditions=plan_data.get('building_conditions'),
                    document_url=plan_data.get('document_url'),
                    wms_url=plan_data.get('wms_url'),
                    wfs_url=plan_data.get('wfs_url'),
                    geometry=geometry_wkt,
                    data_source=plan_data.get('data_source'),
                    is_valid=plan_data.get('is_valid', True),
                )

                db_session.add(plan)
                saved_count += 1

                if saved_count % 50 == 0:
                    db_session.commit()

            except Exception as e:
                logger.warning(f"Error saving plan: {e}")
                continue

        db_session.commit()
        return saved_count
