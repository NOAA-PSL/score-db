"""
Copyright 2023 NOAA
All rights reserved.

Collection of methods to facilitate insertion/selection of experiment
file counts.

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
from score_table_models import ExperimentMetric as ex_mt
from score_table_models import MetricType as mts
from score_table_models import Region as rgs
from experiments import Experiment, ExperimentData
from experiments import ExperimentRequest
import regions as rg
import metric_types as mt
import time_utils
import db_utils


ExptFileCountInputData = namedtuple(
    'ExptFileCountInputData',
    [
        'count',
        'time_valid',
        'experiment_id',
        'file_type_id',
        'storage_location_id'
    ]
)

ExptFileCountData = namedtuple(
    'ExptFileCountData',
    [
        'count',
        'time_valid',
        'experiment_id',
        'file_type_id',
        'storage_location_id',
        'created_at'
    ]
)

class ExptFileCountsError(Exception):
    def __init__(self, m):
        self.message = m
    def __str__(self):
        return self.message
    
@dataclass
class ExptFileCount:
    '''class for storing experiment file count values'''
    count: int
    time_valid: datetime 
    experiment_id: int
    file_type_id: int
    storage_location_id: int
    expt_file_count_data: ExptFileCountData = field(init=False)

    def __post_init__(self):
        self.expt_file_count_data = ExptFileCountData(
            self.count,
            self.time_valid,
            self.experiment_id,
            self.file_type_id,
            self.storage_location_id
        )
    
    def __repr__(self):
        return f'expt_file_count_data: {self.expt_file_count_data}'
    
    def get_expt_file_count_data(self):
        return self.expt_file_count_data
    
def get_file_count_from_body(body):
    if not isinstance(body, dict):
        msg = 'The \'body\' key must be a type dict, actually ' \
            f'{type(body)}'
        raise TypeError(msg)
    
    experiment_id = get_experiment_id(body.get('experiment_name'), body.get('wallclock_start'))
    file_type_id = get_file_type_id(body.get('file_type_name'), body.get('file_extension'))
    storage_location_id = get_storage_location_id(body.get('storage_loc_name'), body.get('storage_loc_platform'), body.get('storage_loc_key')) 

    file_count = ExptFileCount(
        body.get('count'),
        body.get('time_valid'),
        experiment_id,
        file_type_id,
        storage_location_id
    )

    return file_count
    
def get_time_filter(filter_dict, cls, key, constructed_filter):
    if not isinstance(filter_dict, dict):
        msg = f'Invalid type for filters, must be \'dict\', actually ' \
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
        msg = f'string values must be a list - actually: {type(values)}'
        raise TypeError(msg)
    
    for value in values:
        if not isinstance(value, str):
            msg = 'all values must be string type - value: ' \
                f'{value} is type: {type(value)}'
            raise TypeError(msg)
    
    return values

def get_string_filter(filter_dict, cls, key, constructed_filter, key_name):
    if not isinstance(filter_dict, dict):
        msg = f'Invalid type for filters, must be \'dict\', actually ' \
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

def get_experiments_filter(filter_dict, constructed_filter):
    if not isinstance(filter_dict, dict):
        msg = f'Invalid type for filter, must be \'dict\', actually ' \
            f'type: {type(filter_dict)}'
        raise TypeError(msg)
    
    if not isinstance(constructed_filter, dict):
        msg = 'Invalid type for constructed_filter, must be \'dict\', ' \
            f'actually type: {type(filter_dict)}'
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

def get_experiment_id(experiment_name, wallclock_start):
    expt_request = {
        'name': 'experiment',
        'method': db_utils.HTTP_GET,
        'params': {
            'filters': {
                'name': {
                    'exact': experiment_name
                },
                'wallclock_start': {
                    'exact': wallclock_start
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
            record_cnt = records.shape[0]
        else:
            msg = f'Problems encountered requesting experiment data.'
            # create error return db_action_response
            raise ExptFileCountsError(msg)
        if record_cnt <= 0:
            msg = 'Request for experiment record did not return a record'
            raise ExptFileCountsError(msg)
        
    except Exception as err:
        msg = f'Problems encountered requesting experiment data. err - {err}'
        raise ExptFileCountsError(msg)
    
    try:
        record = records[0]
        expt_id = record[exp.id.name].iat[0]
    except Exception as err:
        error_msg = f'Problem finding experiment id from record: {record} '\
            f'- err: {err}'
        print(f'error_msg: {error_msg}')
        raise ExptFileCountsError(error_msg)
    return expt_id


def get_file_type_id(file_type_name, file_extension):
    #TODO: write function
    type_request = {
    
    }
    file_type_id = -1 
    return file_type_id

def get_storage_location_id(storage_loc_name, storage_loc_platform, storage_loc_key):
    #TODO: write function
    type_request={

    }
    storage_loc_id = -1
    return storage_loc_id


@dataclass
class ExptFileCountRequest:
    request_dict: dict
    method: str = field(default_factory=str, init=False)
    params: dict = field(default_factory=dict, init=False)
    filters: dict = field(default_factory=dict, init=False)
    ordering: list = field(default_factory=list, init=False)
    record_limit: int = field(default_factory=int, init=False)
    body: dict = field(default_factory=dict, init=False)
    expt_file_count: ExptFileCount = field(init=False)
    expt_file_count_data: namedtuple = field(init=False)
    response: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.method = db_utils.validate_method(self.request_dict.get('method'))
        self.params = self.request_dict.get('params')
        self.body = self.request_dict.get('body')

        if self.method == db_utils.HTTP_PUT:
            self.expt_file_count = get_file_count_from_body(self.body)
            self.expt_file_count_data = self.expt_file_count.get_expt_file_count_data()
            for k, v in zip(
                self.expt_file_count_data._fields, self.expt_file_count_data
            ):
                val = pprint.pformat(v, indent=4)
                print(f'exp_data: k: {k}, v: {val}')
        else:
            print(f'In ExptFileCountRequest - params: {self.params}')
            if isinstance(self.params, dict):
                self.filters = construct_filters(self.params.get('filters'))
                self.ordering = self.params.get('ordering')
                self.record_limit = self.params.get('record_limit')

                if not type(self.record_limit) == int or self.record_limit <= 0:
                    self.record_limit = None
            else:
                self.filters = None
                self.ordering = None
                self.record_limit = None
    
    def failed_request(self, error_msg):
        return DbActionResponse(
            request=self.request_dict,
            success=False,
            message= 'Failed file type request.',
            details=None,
            errors=error_msg
        )
    
    def submit(self):
        if self.method == db_utils.HTTP_GET:
            
        #TODO: write this out 
