"""Database models for AgentKataster."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    Text, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship, DeclarativeBase
from geoalchemy2 import Geometry
import enum


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class ProcessingStatus(enum.Enum):
    """Status of data processing."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Voivodeship(Base):
    """Województwo (Voivodeship) - highest level administrative division."""
    __tablename__ = "voivodeships"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    geometry = Column(Geometry('MULTIPOLYGON', srid=2180))  # EPSG:2180 - Polish coordinate system

    # Relationships
    counties = relationship("County", back_populates="voivodeship")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class County(Base):
    """Powiat (County) - second level administrative division."""
    __tablename__ = "counties"

    id = Column(Integer, primary_key=True)
    voivodeship_id = Column(Integer, ForeignKey("voivodeships.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    geometry = Column(Geometry('MULTIPOLYGON', srid=2180))

    # Relationships
    voivodeship = relationship("Voivodeship", back_populates="counties")
    municipalities = relationship("Municipality", back_populates="county")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_county_code', 'code'),
    )


class Municipality(Base):
    """Gmina (Municipality) - third level administrative division."""
    __tablename__ = "municipalities"

    id = Column(Integer, primary_key=True)
    county_id = Column(Integer, ForeignKey("counties.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False)  # TERYT code
    type = Column(String(50))  # miejska, wiejska, miejsko-wiejska
    geometry = Column(Geometry('MULTIPOLYGON', srid=2180))

    # Processing status
    parcels_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    parcels_processed_at = Column(DateTime, nullable=True)
    plans_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    plans_processed_at = Column(DateTime, nullable=True)

    # Statistics
    total_parcels = Column(Integer, default=0)
    total_area_m2 = Column(Float, default=0.0)

    # Relationships
    county = relationship("County", back_populates="municipalities")
    parcels = relationship("Parcel", back_populates="municipality")
    spatial_plans = relationship("SpatialPlan", back_populates="municipality")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_municipality_code', 'code'),
        Index('ix_municipality_status', 'parcels_status', 'plans_status'),
    )


class Parcel(Base):
    """Działka (Land Parcel)."""
    __tablename__ = "parcels"

    id = Column(Integer, primary_key=True)
    municipality_id = Column(Integer, ForeignKey("municipalities.id"), nullable=False)

    # Parcel identification
    parcel_id = Column(String(50), nullable=False)  # Numer działki
    register_unit = Column(String(100))  # Jednostka ewidencyjna
    precinct = Column(String(100))  # Obręb
    sheet_number = Column(String(50))  # Numer arkusza mapy

    # Parcel details
    area_m2 = Column(Float, nullable=False)  # Powierzchnia w m2
    area_ha = Column(Float)  # Powierzchnia w ha
    geometry = Column(Geometry('MULTIPOLYGON', srid=2180), nullable=False)

    # Land use
    land_use_code = Column(String(10))  # Kod użytku gruntowego (R, Ł, Ps, etc.)
    land_use_description = Column(String(200))  # Opis użytku

    # Additional metadata
    data_source = Column(String(100))  # Źródło danych
    data_quality = Column(String(50))  # Klasa dokładności

    # Relationships
    municipality = relationship("Municipality", back_populates="parcels")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_parcel_id', 'parcel_id'),
        Index('ix_parcel_municipality', 'municipality_id'),
        Index('ix_parcel_area', 'area_m2'),
        Index('ix_parcel_land_use', 'land_use_code'),
        Index('ix_parcel_geometry', 'geometry', postgresql_using='gist'),
    )


class SpatialPlanType(enum.Enum):
    """Type of spatial development plan."""
    MPZP = "mpzp"  # Miejscowy Plan Zagospodarowania Przestrzennego (Local)
    SUIKZP = "suikzp"  # Studium Uwarunkowań i Kierunków (General)
    OTHER = "other"


class SpatialPlan(Base):
    """Plan zagospodarowania przestrzennego (Spatial Development Plan)."""
    __tablename__ = "spatial_plans"

    id = Column(Integer, primary_key=True)
    municipality_id = Column(Integer, ForeignKey("municipalities.id"), nullable=False)

    # Plan identification
    plan_type = Column(SQLEnum(SpatialPlanType), nullable=False)
    name = Column(String(500), nullable=False)
    number = Column(String(100))  # Numer uchwały

    # Legal information
    adoption_date = Column(DateTime)  # Data uchwalenia
    publication_date = Column(DateTime)  # Data publikacji
    effective_date = Column(DateTime)  # Data wejścia w życie

    # Plan details
    description = Column(Text)
    area_m2 = Column(Float)
    geometry = Column(Geometry('MULTIPOLYGON', srid=2180))

    # Zoning information (for MPZP)
    zoning_code = Column(String(50))  # Symbol przeznaczenia (MN, U, P, etc.)
    zoning_description = Column(Text)  # Opis przeznaczenia
    building_conditions = Column(Text)  # Warunki zabudowy

    # Documents
    document_url = Column(String(500))  # URL do dokumentu planu
    wms_url = Column(String(500))  # URL do warstwy WMS
    wfs_url = Column(String(500))  # URL do warstwy WFS

    # Metadata
    data_source = Column(String(200))
    is_valid = Column(Boolean, default=True)  # Czy plan jest aktualny

    # Relationships
    municipality = relationship("Municipality", back_populates="spatial_plans")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_plan_municipality', 'municipality_id'),
        Index('ix_plan_type', 'plan_type'),
        Index('ix_plan_zoning', 'zoning_code'),
        Index('ix_plan_geometry', 'geometry', postgresql_using='gist'),
    )


class ScraperLog(Base):
    """Log of scraping operations."""
    __tablename__ = "scraper_logs"

    id = Column(Integer, primary_key=True)
    municipality_id = Column(Integer, ForeignKey("municipalities.id"), nullable=True)

    operation_type = Column(String(50), nullable=False)  # parcels, plans, municipalities
    status = Column(SQLEnum(ProcessingStatus), nullable=False)

    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    error_message = Column(Text, nullable=True)
    extra_metadata = Column(Text, nullable=True)  # JSON with additional info

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_scraper_log_municipality', 'municipality_id'),
        Index('ix_scraper_log_status', 'status'),
        Index('ix_scraper_log_created', 'created_at'),
    )
