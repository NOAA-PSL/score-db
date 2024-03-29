"""
Copyright 2022 NOAA
All rights reserved.

Collection of methods to facilitate file/object retrieval

"""
import enum
import os
from dotenv import load_dotenv
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import Integer, String, Boolean, DateTime, Float, BigInteger

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import inspect, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.dialects import postgresql
from geoalchemy2.types import Geography, Geometry

EXPERIMENTS_TABLE = 'experiments'
EXPERIMENT_METRICS_TABLE = 'expt_metrics'
REGIONS_TABLE = 'regions'
METRIC_TYPES_TABLE = 'metric_types'
STORAGE_LOCATION_TABLE = 'storage_locations'
FILE_TYPES_TABLE = 'file_types'
EXPT_STORED_FILE_COUNTS_TABLE = 'expt_stored_file_counts'


# temporary use dotenv to load the db environment
load_dotenv()

def get_engine(user, passwd, host, port, db):
    url = f'postgresql://{user}:{passwd}@{host}:{port}/{db}'
    if not database_exists(url):
        create_database(url)

    db_engine = create_engine(
        url,
        pool_size=50,
        echo=False,
        connect_args={"options": "-c timezone=utc"}
    )

    return db_engine


def get_engine_from_settings():

    return get_engine(
        os.getenv('SCORE_POSTGRESQL_DB_USERNAME'),
        os.getenv('SCORE_POSTGRESQL_DB_PASSWORD'),
        os.getenv('SCORE_POSTGRESQL_DB_ENDPOINT'),
        os.getenv('SCORE_POSTGRESQL_DB_PORT'),
        os.getenv('SCORE_POSTGRESQL_DB_NAME'))


engine = get_engine_from_settings()
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Platforms(enum.Enum):
    HERA = 1
    ORION = 2
    AZPW_V1 = 3
    AZPW_V2 = 4


class Experiment(Base):
    __tablename__ = EXPERIMENTS_TABLE
    __table_args__ = (
        UniqueConstraint(
            'name',
            'wallclock_start',
            name='unique_experiment'
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    cycle_start = Column(DateTime, nullable=False)
    cycle_stop = Column(DateTime, nullable=False)
    owner_id = Column(String(64), nullable=False)
    group_id = Column(String(16))
    experiment_type = Column(String(64))
    #   platform = Column(sa.Enum('Hera','Orion', 'azpw_v1','azpw_v2', 'awpw_v1', name='platform_name'))
    platform = Column(String(16), nullable=False)
    wallclock_start = Column(DateTime, nullable=False)
    wallclock_end = Column(DateTime)
    description = Column(JSONB(astext_type=sa.Text()), nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    metrics = relationship('ExperimentMetric', back_populates='experiment')
    file_counts = relationship('ExptStoredFileCount', back_populates='experiment')


class ExperimentMetric(Base):
    __tablename__ = EXPERIMENT_METRICS_TABLE

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id'))
    metric_type_id = Column(Integer, ForeignKey('metric_types.id'))
    region_id = Column(Integer, ForeignKey('regions.id'))
    elevation = Column(Float)
    elevation_unit = Column(String(32))
    value = Column(Float)
    time_valid = Column(DateTime, nullable=False)
    forecast_hour = Column(Float)
    ensemble_member = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow())

    experiment = relationship('Experiment', back_populates='metrics')
    metric_type = relationship('MetricType', back_populates='metrics')
    region = relationship('Region', back_populates='metrics')


class Region(Base):
    __tablename__ = REGIONS_TABLE
    __table_args__ = (
        UniqueConstraint('min_lat', 'max_lat',
                         'east_lon', 'west_lon', name='unique_region'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(79), nullable=False)
    min_lat = Column(Float, nullable=False)
    max_lat = Column(Float, nullable=False)
    east_lon = Column(Float, nullable=False)
    west_lon = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)

    metrics = relationship('ExperimentMetric', back_populates='region')


class MetricType(Base):
    __tablename__ = METRIC_TYPES_TABLE
    __table_args__ = (
        UniqueConstraint(
            'name',
            'measurement_type',
            'measurement_units',
            'stat_type',
            name='unique_metric_type'
        ),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    long_name = Column(String(128))
    measurement_type = Column(String(64), nullable=False)
    measurement_units = Column(String(64))
    stat_type = Column(String(64))
    description = Column(JSONB(astext_type=sa.Text()), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    
    metrics = relationship('ExperimentMetric', back_populates='metric_type')

class StorageLocation(Base):
    __tablename__ = STORAGE_LOCATION_TABLE
    __table_args__ = (
        UniqueConstraint(
            'name',
            'platform',
            'bucket_name',
            'key',
            name='unique_storage_location'
        ),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    platform = Column(String(128), nullable=False)   
    bucket_name = Column(String(128), nullable=False)
    key = Column(String(128))
    platform_region = Column(String(64))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    file_counts = relationship('ExptStoredFileCount', back_populates='storage_location')

class ExptStoredFileCount(Base):
    __tablename__ = EXPT_STORED_FILE_COUNTS_TABLE

    id = Column(Integer, primary_key=True, autoincrement=True)
    storage_location_id = Column(Integer, ForeignKey('storage_locations.id'))
    file_type_id = Column(Integer, ForeignKey('file_types.id'))
    experiment_id = Column(Integer, ForeignKey('experiments.id'))
    count = Column(Float, nullable=False)
    folder_path = Column(String(255))
    cycle = Column(DateTime)
    time_valid = Column(DateTime)
    forecast_hour = Column(Float)
    file_size_bytes = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow())

    experiment = relationship('Experiment', back_populates='file_counts')
    file_type = relationship('FileType', back_populates='file_counts')
    storage_location = relationship('StorageLocation', back_populates='file_counts')


class FileType(Base):
    __tablename__ = FILE_TYPES_TABLE
    __table_args__ = (
        UniqueConstraint(
            'name',
            name='unique_file_type'
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    file_template= Column(String(64), nullable=False)
    file_format = Column(String(64))
    description = Column(JSONB(astext_type=sa.Text()), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    
    file_counts = relationship('ExptStoredFileCount', back_populates='file_type')
    

Base.metadata.create_all(engine)

def get_session():
    engine = get_engine_from_settings()
    Session = sessionmaker(bind=engine)

    return Session()
