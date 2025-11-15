"""Scraper for ULDK (cadastral parcel data)."""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime

from loguru import logger
from geopandas import GeoDataFrame
from shapely import wkt
from shapely.geometry import shape
import geopandas as gpd

from .base_scraper import BaseScraper
from ..models import Municipality, Parcel, ProcessingStatus
from ..config import settings


class ULDKScraper(BaseScraper):
    """
    Scraper for ULDK (Usługi Lokalizacji Działek Katastralnych).

    ULDK provides WFS access to cadastral parcel boundaries in Poland.
    """

    def __init__(self):
        super().__init__()
        self.wfs_url = "https://uldk.gugik.gov.pl/service.svc/get"

    async def get_municipalities(self) -> List[Dict[str, Any]]:
        """
        Get list of all municipalities from ULDK.

        Returns:
            List of municipality dictionaries with TERYT codes and names
        """
        logger.info("Fetching municipalities from ULDK...")

        params = {
            'request': 'GetUnitsInfo',
            'level': '9',  # Municipality level
        }

        try:
            response = await self._make_request(
                self.wfs_url,
                params=params
            )

            if not response:
                return []

            municipalities = self._parse_municipalities(response)
            logger.info(f"Found {len(municipalities)} municipalities")
            return municipalities

        except Exception as e:
            logger.error(f"Error fetching municipalities: {e}")
            return []

    def _parse_municipalities(self, xml_data: str) -> List[Dict[str, Any]]:
        """Parse municipalities from XML response."""
        municipalities = []

        try:
            root = ET.fromstring(xml_data)

            # Parse XML structure (adjust based on actual ULDK response format)
            for unit in root.findall('.//jednostka'):
                municipality = {
                    'code': unit.find('teryt').text if unit.find('teryt') is not None else None,
                    'name': unit.find('nazwa').text if unit.find('nazwa') is not None else None,
                    'type': unit.find('typ').text if unit.find('typ') is not None else None,
                }
                if municipality['code'] and municipality['name']:
                    municipalities.append(municipality)

        except ET.ParseError as e:
            logger.error(f"Error parsing municipalities XML: {e}")

        return municipalities

    async def get_parcels_for_municipality(
        self,
        teryt_code: str,
        municipality_name: str
    ) -> Optional[GeoDataFrame]:
        """
        Get all parcels for a specific municipality.

        Args:
            teryt_code: TERYT code of municipality
            municipality_name: Name of municipality

        Returns:
            GeoDataFrame with parcel geometries and attributes
        """
        logger.info(f"Fetching parcels for {municipality_name} ({teryt_code})")

        # ULDK WFS request for parcels
        params = {
            'request': 'GetParcelByIdOrNr',
            'id': teryt_code,
            'result': 'geom_wkt',  # Request WKT geometry
        }

        try:
            response = await self._make_request(
                self.wfs_url,
                params=params
            )

            if not response:
                logger.warning(f"No response for municipality {teryt_code}")
                return None

            parcels_gdf = self._parse_parcels(response, teryt_code)

            if parcels_gdf is not None and not parcels_gdf.empty:
                logger.info(
                    f"Found {len(parcels_gdf)} parcels for {municipality_name}"
                )
            else:
                logger.warning(f"No parcels found for {municipality_name}")

            return parcels_gdf

        except Exception as e:
            logger.error(f"Error fetching parcels for {teryt_code}: {e}")
            return None

    def _parse_parcels(
        self,
        xml_data: str,
        teryt_code: str
    ) -> Optional[GeoDataFrame]:
        """Parse parcels from XML/GML response."""
        parcels = []

        try:
            root = ET.fromstring(xml_data)

            # Parse GML/XML structure (adjust namespace based on actual response)
            namespaces = {
                'gml': 'http://www.opengis.net/gml',
                'uldk': 'http://uldk.gugik.gov.pl'
            }

            for parcel_elem in root.findall('.//dzialka', namespaces):
                try:
                    parcel_data = {
                        'parcel_id': self._get_text(parcel_elem, 'identyfikator'),
                        'register_unit': self._get_text(parcel_elem, 'jednostka_ewid'),
                        'precinct': self._get_text(parcel_elem, 'obreb'),
                        'sheet_number': self._get_text(parcel_elem, 'arkusz'),
                        'area_m2': float(self._get_text(parcel_elem, 'powierzchnia', '0')),
                        'land_use_code': self._get_text(parcel_elem, 'klasa_uzytkowania'),
                        'geometry_wkt': self._get_text(parcel_elem, 'geometria_wkt'),
                    }

                    # Parse WKT geometry
                    if parcel_data['geometry_wkt']:
                        parcel_data['geometry'] = wkt.loads(parcel_data['geometry_wkt'])
                    else:
                        continue  # Skip parcels without geometry

                    # Calculate area in hectares
                    parcel_data['area_ha'] = parcel_data['area_m2'] / 10000

                    parcels.append(parcel_data)

                except Exception as e:
                    logger.warning(f"Error parsing parcel: {e}")
                    continue

            if parcels:
                gdf = gpd.GeoDataFrame(
                    parcels,
                    crs="EPSG:2180",  # Polish coordinate system
                    geometry='geometry'
                )
                return gdf
            else:
                return None

        except ET.ParseError as e:
            logger.error(f"Error parsing parcels XML: {e}")
            return None

    def _get_text(
        self,
        element: ET.Element,
        tag: str,
        default: str = None
    ) -> Optional[str]:
        """Safely get text from XML element."""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return default

    async def scrape(
        self,
        municipality_code: str,
        municipality_name: str,
        db_session
    ) -> Dict[str, Any]:
        """
        Main scraping method for a municipality.

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
            'parcels_count': 0,
            'total_area_m2': 0.0,
            'status': ProcessingStatus.IN_PROGRESS.value,
            'error': None
        }

        try:
            # Get parcels
            parcels_gdf = await self.get_parcels_for_municipality(
                municipality_code,
                municipality_name
            )

            if parcels_gdf is None or parcels_gdf.empty:
                stats['status'] = ProcessingStatus.COMPLETED.value
                stats['parcels_count'] = 0
                return stats

            # Save parcels to database
            municipality = db_session.query(Municipality).filter_by(
                code=municipality_code
            ).first()

            if not municipality:
                logger.error(f"Municipality {municipality_code} not found in database")
                stats['status'] = ProcessingStatus.FAILED.value
                stats['error'] = "Municipality not found in database"
                return stats

            parcels_saved = 0
            total_area = 0.0

            for idx, row in parcels_gdf.iterrows():
                try:
                    parcel = Parcel(
                        municipality_id=municipality.id,
                        parcel_id=row.get('parcel_id'),
                        register_unit=row.get('register_unit'),
                        precinct=row.get('precinct'),
                        sheet_number=row.get('sheet_number'),
                        area_m2=row.get('area_m2', 0.0),
                        area_ha=row.get('area_ha', 0.0),
                        land_use_code=row.get('land_use_code'),
                        geometry=f"SRID=2180;{row['geometry'].wkt}",
                        data_source="ULDK",
                    )

                    db_session.add(parcel)
                    parcels_saved += 1
                    total_area += row.get('area_m2', 0.0)

                    # Commit in batches
                    if parcels_saved % 100 == 0:
                        db_session.commit()
                        logger.info(f"Saved {parcels_saved} parcels...")

                except Exception as e:
                    logger.warning(f"Error saving parcel: {e}")
                    continue

            # Final commit
            db_session.commit()

            # Update municipality statistics
            municipality.total_parcels = parcels_saved
            municipality.total_area_m2 = total_area
            municipality.parcels_status = ProcessingStatus.COMPLETED
            municipality.parcels_processed_at = datetime.utcnow()
            db_session.commit()

            stats['parcels_count'] = parcels_saved
            stats['total_area_m2'] = total_area
            stats['status'] = ProcessingStatus.COMPLETED.value

            logger.info(
                f"Successfully scraped {parcels_saved} parcels "
                f"for {municipality_name} ({municipality_code})"
            )

        except Exception as e:
            logger.error(f"Error scraping municipality {municipality_code}: {e}")
            stats['status'] = ProcessingStatus.FAILED.value
            stats['error'] = str(e)
            db_session.rollback()

        return stats
