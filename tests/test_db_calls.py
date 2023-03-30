"""
Copyright 2022 NOAA
All rights reserved.

Unit tests for io_utils

"""
import os
import pathlib
import pytest
import json

import sqlalchemy as sa
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import Integer, String, Boolean, DateTime, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database


import score_table_models
from score_table_models import Experiment as experiments_table
import experiments as expts
from experiments import ExperimentData, Experiment, ExperimentRequest

from score_db_base import handle_request

import unittest
from unittest.mock import patch 


PYTEST_CALLING_DIR = pathlib.Path(__file__).parent.resolve()
EXPERIMENT_CONFIG_FILE = os.path.join(
    PYTEST_CALLING_DIR,
    'configs',
    'experiment_description.json'
)

# class TestDB:
#     def setup_db(self):
#         engine = create_engine("sqlite://") # uses in-memory database  
#         scr_models.Base.metadata.create_all(engine) # engine should be sqlite
#         Session = sessionmaker(bind=engine) 
#         session = Session()
#         yield session
#         session.close()


@pytest.fixture(scope='module')
def mock_engine():
    engine = create_engine("sqlite://")
    create_database(engine.url)
    return engine

# mock score_table_models.get_engine_from_settings with create_engine("sqlite://")

@patch.object(score_table_models, 'get_engine_from_settings')
def test_database_something(self, mock_engine):
    # engine = create_engine("sqlite://")
    # create_database(engine.url)
    # mock_engine.return_call = engine

    request_dict = {
        'name': 'experiment',
        'method': 'PUT',
        'body': {
            'name': 'test_expt_123',
            'datestr_format': '%Y-%m-%d %H:%M:%S',
            'cycle_start': '2016-01-01 00:00:00',
            'cycle_stop': '2016-01-31 18:00:00',
            'owner_id': 'test.owner@noaa.gov',
            'group_id': 'gsienkf',
            'experiment_type': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'platform': 'pw_awv1',
            'wallclock_start': '2021-07-22 09:22:05',
            'wallclock_end': '2021-07-24 05:31:14',
            'description': '{"unstructured_json": "data"}'
        }
    }

    er = ExperimentRequest(request_dict)
    er.submit()

    metadata = sa.MetaData()
    experiments = sa.Table('experiments', metadata, autoload=True, autoload_with=mock_engine())
    number = 2


    

    