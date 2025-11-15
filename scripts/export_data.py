#!/usr/bin/env python
"""Export collected data to various formats."""
import argparse
from pathlib import Path

import geopandas as gpd
from sqlalchemy import create_engine
from loguru import logger

from src.config import settings
from src.models import Parcel, SpatialPlan, Municipality


def export_parcels_to_geojson(
    municipality_code: str = None,
    output_file: str = "parcels.geojson"
):
    """Export parcels to GeoJSON format."""
    logger.info("Exporting parcels to GeoJSON...")

    engine = create_engine(settings.database_url)

    # Build query
    query = """
    SELECT
        p.id,
        p.parcel_id,
        p.register_unit,
        p.precinct,
        p.area_m2,
        p.area_ha,
        p.land_use_code,
        m.name as municipality_name,
        m.code as municipality_code,
        ST_AsText(p.geometry) as geometry
    FROM parcels p
    JOIN municipalities m ON p.municipality_id = m.id
    """

    if municipality_code:
        query += f" WHERE m.code = '{municipality_code}'"

    # Read to GeoDataFrame
    gdf = gpd.read_postgis(
        query,
        engine,
        geom_col='geometry',
        crs='EPSG:2180'
    )

    # Transform to WGS84 for web use
    gdf = gdf.to_crs('EPSG:4326')

    # Save to GeoJSON
    gdf.to_file(output_file, driver='GeoJSON')

    logger.info(f"Exported {len(gdf)} parcels to {output_file}")
    return output_file


def export_plans_to_geojson(
    municipality_code: str = None,
    output_file: str = "spatial_plans.geojson"
):
    """Export spatial plans to GeoJSON format."""
    logger.info("Exporting spatial plans to GeoJSON...")

    engine = create_engine(settings.database_url)

    query = """
    SELECT
        sp.id,
        sp.plan_type,
        sp.name,
        sp.number,
        sp.zoning_code,
        sp.zoning_description,
        sp.adoption_date,
        sp.is_valid,
        m.name as municipality_name,
        m.code as municipality_code,
        ST_AsText(sp.geometry) as geometry
    FROM spatial_plans sp
    JOIN municipalities m ON sp.municipality_id = m.id
    WHERE sp.geometry IS NOT NULL
    """

    if municipality_code:
        query += f" AND m.code = '{municipality_code}'"

    gdf = gpd.read_postgis(
        query,
        engine,
        geom_col='geometry',
        crs='EPSG:2180'
    )

    # Transform to WGS84
    gdf = gdf.to_crs('EPSG:4326')

    # Save to GeoJSON
    gdf.to_file(output_file, driver='GeoJSON')

    logger.info(f"Exported {len(gdf)} spatial plans to {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Export AgentKataster data to GeoJSON"
    )
    parser.add_argument(
        '--type',
        choices=['parcels', 'plans', 'both'],
        default='both',
        help='Type of data to export'
    )
    parser.add_argument(
        '--municipality',
        help='TERYT code of municipality (optional)'
    )
    parser.add_argument(
        '--output-dir',
        default='exports',
        help='Output directory'
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    if args.type in ['parcels', 'both']:
        parcels_file = output_dir / 'parcels.geojson'
        export_parcels_to_geojson(
            municipality_code=args.municipality,
            output_file=str(parcels_file)
        )

    if args.type in ['plans', 'both']:
        plans_file = output_dir / 'spatial_plans.geojson'
        export_plans_to_geojson(
            municipality_code=args.municipality,
            output_file=str(plans_file)
        )

    print(f"\n✓ Export complete! Files saved to {output_dir}/")


if __name__ == '__main__':
    main()
