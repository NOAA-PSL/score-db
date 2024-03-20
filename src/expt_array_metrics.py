"""
Copyright NOAA 2024
All rights reserved.

Collection of methods to facilitate handling of requests for array based experiment metrics.
Will also interact with the experiments, regions, array metric types, and sat meta tables. 
"""

from collections import namedtuple
import copy
from dataclasses import dataclass, field
from datetime import datetime
import json
import math
import pprint
import traceback

import numpy as np
from psycopg2.extensions import register_adapter, AsIs
from sqlalchemy import Integer, String, Boolean, DateTime, Float
import psycopg2
import pandas as pd
from pandas import DataFrame
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.inspection import inspect
from sqlalchemy import and_, or_, not_
from sqlalchemy import asc, desc
from sqlalchemy.sql import func
from sqlalchemy.orm import joinedload


from db_action_response import DbActionResponse
import score_table_models as stm
from score_table_models import Experiment as exp
from score_table_models import ArrayExperimentMetric as arr_ex_mt
from score_table_models import ArrayMetricType as amt
from score_table_models import SatMeta as sm
from score_table_models import Region as rgs
from experiments import Experiment, ExperimentData
from experiments import ExperimentRequest
import regions as rg
import array_metric_types as amt
import time_utils
import db_utils

psycopg2.extensions.register_adapter(np.int64, psycopg2._psycopg.AsIs)
psycopg2.extensions.register_adapter(np.float32, psycopg2._psycopg.AsIs)

ExptArrayMetricInputData = namedtuple(
    'ExptArrayMetricInputData',
    [
        'value',
        'bias_correction',
        'assimilated',
        'time_valid',
        'forecast_hour',
        'ensemble_member'
    ],
) 

#edit as necessary for this section
ExptArrayMetricsData = namedtuple(
    'ExptArrayMetricsData',
    [
        'id',
        'name',
        'elevation',
        'elevation_unit',
        'value',
        'bias_correction',
        'time_valid',
        'forecast_hour',
        'ensemble_member',
        'expt_id',
        'expt_name',
        'wallclock_start',
        'metric_id',
        'metric_long_name',
        'metric_type',
        'metric_unit',
        'metric_stat_type',
        'region_id',
        'region',
        'created_at'
    ],
)

class ExptArrayMetricsError(Exception):
    def __init__(self, m):
        self.message = m
    def __str__(self):
        return self.message
    
def get_time_filter(filter_dict, cls, key, constructed_filter):
    if not isinstance(filter_dict, dict):
        msg = f'Invalid type for filters, must be \'dict\', was ' \
            f'type: {type(filter_dict)}'
        raise TypeError(msg)

    value = filter_dict.get(key)
    if value is None:
        print(f'No \'{key}\' filter detected')
        return constructed_filter

    exact_datetime = time_utils.get_time(value.get(db_utils.EXACT_DATETIME))

    if exact_datetime is not None:
        constructed_filter[key] = (
            getattr(cls, key) == exact_datetime
        )
        return constructed_filter

    from_datetime = time_utils.get_time(value.get(db_utils.FROM_DATETIME))
    to_datetime = time_utils.get_time(value.get(db_utils.TO_DATETIME))

    if from_datetime is not None and to_datetime is not None:
        if to_datetime < from_datetime:
            raise ValueError('\'from\' must be older than \'to\'')
        
        constructed_filter[key] = and_(
            getattr(cls, key) >= from_datetime,
            getattr(cls, key) <= to_datetime
        )
    elif from_datetime is not None:
        constructed_filter[key] = (
            getattr(cls, key) >= from_datetime
        )
    elif to_datetime is not None:
        constructed_filter[key] = (
            getattr(cls, key) <= to_datetime
        )

    return constructed_filter


def validate_list_of_strings(values):
    if isinstance(values, str):
        val_list = []
        val_list.append(values)
        return val_list

    if not isinstance(values, list):
        msg = f'string values must be a list, was: {type(values)}'
        raise TypeError(msg)
    
    for value in values:
        if not isinstance(value, str):
            msg = 'all values must be string type - value: ' \
                f'{value} is type: {type(value)}'
            raise TypeError(msg)
    
    return values


def get_string_filter(filter_dict, cls, key, constructed_filter, key_name):
    if not isinstance(filter_dict, dict):
        msg = f'Invalid type for filters, must be \'dict\', was ' \
            f'type: {type(filter_dict)}'
        raise TypeError(msg)

    print(f'Column \'{key}\' is of type {type(getattr(cls, key).type)}.')
    string_flt = filter_dict.get(key)
    print(f'string_flt: {string_flt}')

    if string_flt is None:
        print(f'No \'{key}\' filter detected')
        return constructed_filter

    like_filter = string_flt.get('like')
    # prefer like search over exact match if both exist
    if like_filter is not None:
        constructed_filter[key_name] = (getattr(cls, key).like(like_filter))
        return constructed_filter

    exact_match_filter = validate_list_of_strings(string_flt.get('exact'))
    if exact_match_filter is not None:
        constructed_filter[key_name] = (getattr(cls, key).in_(exact_match_filter))

    return constructed_filter

def get_float_filter(filter_dict, cls, key, constructed_filter):
    if not isinstance(filter_dict, dict):
        msg = f'Invalid type for filters, must be \'dict\', was ' \
            f'type: {type(filter_dict)}'
        raise TypeError(msg)

    print(f'Column \'{key}\' is of type {type(getattr(cls, key).type)}.')
    float_flt = filter_dict.get(key)

    if float_flt is None:
        print(f'No \'{key}\' filter detected')
        return constructed_filter

    constructed_filter[key] = ( getattr(cls, key) == float_flt )
    
    return constructed_filter

def get_experiments_filter(filter_dict, constructed_filter):
    if not isinstance(filter_dict, dict):
        msg = f'Invalid type for filter, must be \'dict\', was ' \
            f'type: {type(filter_dict)}'
        raise TypeError(msg)
    
    if not isinstance(constructed_filter, dict):
        msg = 'Invalid type for constructed_filter, must be \'dict\', ' \
            f'was type: {type(filter_dict)}'
        raise TypeError(msg)   
    
    constructed_filter = get_string_filter(
        filter_dict, exp, 'name', constructed_filter, 'experiment_name')
    
    constructed_filter = get_time_filter(
        filter_dict, exp, 'cycle_start', constructed_filter)

    constructed_filter = get_time_filter(
        filter_dict, exp, 'cycle_stop', constructed_filter)

    constructed_filter = get_time_filter(
        filter_dict, exp, 'wallclock_start', constructed_filter)
    
    return constructed_filter

def get_array_metric_types_filter(filter_dict, constructed_filter):
    if filter_dict is None:
        return constructed_filter
    
    if not isinstance(filter_dict, dict):
        msg = f'Invalid type for filter, must be \'dict\', was ' \
            f'type: {type(filter_dict)}'
        raise TypeError(msg)
    
    if not isinstance(constructed_filter, dict):
        msg = 'Invalid type for constructed_filter, must be \'dict\', ' \
            f'was type: {type(filter_dict)}'
        raise TypeError(msg)

    constructed_filter = get_string_filter(filter_dict, amt, 'name', constructed_filter, 'name')
    
    constructed_filter = get_string_filter(filter_dict, amt, 'long_name', constructed_filter, 'long_name')
    
    constructed_filter = get_string_filter(filter_dict, amt, 'obs_platform', constructed_filter, 'obs_platform')

    constructed_filter = get_string_filter(filter_dict, amt, 'measurement_type', constructed_filter, 'measurement_type')

    constructed_filter = get_string_filter(filter_dict, amt, 'measurement_units', constructed_filter, 'measurement_units')

    constructed_filter = get_string_filter(filter_dict, amt, 'stat_type', constructed_filter, 'stat_type')
    
    constructed_filter = get_string_filter(filter_dict, sm, 'name', constructed_filter, 'sat_meta_name')

    return constructed_filter   

def get_regions_filter(filter_dict, constructed_filter):
    if filter_dict is None:
        return constructed_filter

    if not isinstance(filter_dict, dict):
        msg = f'Invalid type for filter, must be \'dict\', was ' \
            f'type: {type(filter_dict)}'
        raise TypeError(msg)
    
    if not isinstance(constructed_filter, dict):
        msg = 'Invalid type for constructed_filter, must be \'dict\', ' \
            f'was type: {type(filter_dict)}'
        raise TypeError(msg)

    constructed_filter = get_string_filter(
        filter_dict, rgs, 'name', constructed_filter, 'rgs_name')

    constructed_filter = get_float_filter(filter_dict, rgs, 'min_lat', constructed_filter)

    constructed_filter = get_float_filter(filter_dict, rgs, 'max_lat', constructed_filter)

    constructed_filter = get_float_filter(filter_dict, rgs, 'east_lon', constructed_filter)

    constructed_filter = get_float_filter(filter_dict, rgs, 'west_lon', constructed_filter)

    return constructed_filter

def get_expt_record_id(body):
    expt_name = body.get('expt_name')
    wlclk_strt_str = body.get('expt_wallclock_start')
    
    expt_request = {
        'name': 'experiment',
        'method': db_utils.HTTP_GET,
        'params': {
            'filters': {
                'name': {
                    'exact': expt_name
                },
                'wallclock_start': {
                    'exact': wlclk_strt_str
                },
            },
            'ordering': [
                {'name': 'wallclock_start', 'order_by': 'desc'}
            ],
            'record_limit': 1
        }
    }

    print(f'expt_request: {expt_request}')

    er = ExperimentRequest(expt_request)

    results = er.submit()
    print(f'results: {results}')

    record_cnt = 0
    try:
        if results.success is True:
            records = results.details.get('records')
            if records is None:
                msg = 'Request for experiment record did not return a record'
                raise ExptArrayMetricsError(msg)
            record_cnt = records.shape[0]
        else:
            msg = f'Problems encountered requesting experiment data.'
            # create error return db_action_response
            raise ExptArrayMetricsError(msg)
        if record_cnt <= 0:
            msg = 'Request for experiment record did not return a record'
            raise ExptArrayMetricsError(msg)
        
    except Exception as err:
        msg = f'Problems encountered requesting experiment data. err - {err}'
        raise ExptArrayMetricsError(msg)
    
    try:
        experiment_id = records[exp.id.name].iat[0]
    except Exception as err:
        error_msg = f'Problem finding experiment id from record: {records} ' \
            f'- err: {err}'
        print(f'error_msg: {error_msg}')
        raise ExptArrayMetricsError(error_msg) 
        
    return experiment_id

##TODO: request class 