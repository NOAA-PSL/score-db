"""
Copyright 2022 NOAA
All rights reserved.

Collection of methods to facilitate handling of requests for experiment
metrics (note: in order to request experiment metrics, the experiment
registry, regions, and metric_types tables must also be accessed).

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


from score_db.db_action_response import DbActionResponse
import score_db.score_table_models as stm
from score_db.score_table_models import Experiment as exp
from score_db.score_table_models import ExperimentMetric as ex_mt
from score_db.score_table_models import MetricType as mts
from score_db.score_table_models import Region as rgs
from score_db.score_table_models import SatMeta as sm
from score_db.score_table_models import InstrumentMeta as im
from score_db.experiments import Experiment, ExperimentData
from score_db.experiments import ExperimentRequest
from score_db.sat_meta import SatMetaRequest
from score_db.regions import RegionRequest
import score_db.metric_types as mt
from score_db import time_utils
from score_db import db_utils

psycopg2.extensions.register_adapter(np.int64, psycopg2._psycopg.AsIs)
psycopg2.extensions.register_adapter(np.float32, psycopg2._psycopg.AsIs)

ExptMetricInputData = namedtuple(
    'ExptMetricInputData',
    [
        'name',
        'region_name',
        'region_min_lat',
        'region_max_lat',
        'region_east_lon',
        'region_west_lon',
        'elevation',
        'elevation_unit',
        'value',
        'time_valid',
        'forecast_hour',
        'ensemble_member',
        'sat_meta_name',
        'sat_id',
        'sat_name',
        'sat_short_name',
    ],
)


ExptMetricsData = namedtuple(
    'ExptMetricsData',
    [
        'id',
        'name',
        'elevation',
        'elevation_unit',
        'value',
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
        'metric_stage',
        'metric_obs_platform',
        'metric_instrument_meta_id',
        'metric_instrument_name',
        'metric_instrument_num_channels',
        'region_id',
        'region_name',
        'region_min_lat',
        'region_max_lat',
        'region_east_lon',
        'region_west_lon',
        'sat_meta_id',
        'sat_meta_name',
        'sat_id',
        'sat_name',
        'sat_short_name',
        'created_at'
    ],
)


class ExptMetricsError(Exception):
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
    string_flt = filter_dict.get(key_name)
    print(f'string_flt: {string_flt}')

    if string_flt is None:
        print(f'No \'{key}\' filter detected')
        return constructed_filter

    like_filter = string_flt.get('like')
    # prefer like search over exact match if both exist
    if like_filter is not None:
        constructed_filter[f'{cls.__name__}.{key}'] = (getattr(cls, key).like(like_filter))
        return constructed_filter

    exact_match_filter = validate_list_of_strings(string_flt.get('exact'))
    if exact_match_filter is not None:
        constructed_filter[f'{cls.__name__}.{key}'] = (getattr(cls, key).in_(exact_match_filter))

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

def get_int_filter(filters, cls, key, constructed_filter):
    if not isinstance(filters, dict):
        msg = f'Invalid type for filters, must be \'dict\', was ' \
            f'type: {type(filters)}'
        raise TypeError(msg)

    print(f'Column \'{key}\' is of type {type(getattr(cls, key).type)}.')
    int_flt = filters.get(key)

    if int_flt is None:
        print(f'No \'{key}\' filter detected')
    else:
        constructed_filter[f'{cls.__name__}.{key}'] = ( getattr(cls, key) == int_flt )
    
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
        filter_dict, exp, 'name', constructed_filter, 'name')
    
    constructed_filter = get_time_filter(
        filter_dict, exp, 'cycle_start', constructed_filter)

    constructed_filter = get_time_filter(
        filter_dict, exp, 'cycle_stop', constructed_filter)

    constructed_filter = get_time_filter(
        filter_dict, exp, 'wallclock_start', constructed_filter)
    
    constructed_filter = get_int_filter(
        filter_dict, exp, 'id', constructed_filter)
    
    return constructed_filter


def get_metric_types_filter(filter_dict, constructed_filter):
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
        filter_dict,
        mts,
        'name',
        constructed_filter,
        'name'
    )

    constructed_filter = get_string_filter(
        filter_dict,
        mts,
        'long_name',
        constructed_filter,
        'long_name'
    )
    
    constructed_filter = get_string_filter(
        filter_dict, mts,
        'measurement_type',
        constructed_filter,
        'measurement_type'
    )
    
    constructed_filter = get_string_filter(
        filter_dict, mts,
        'measurement_units',
        constructed_filter,
        'measurement_units'
    )
    
    constructed_filter = get_string_filter(
        filter_dict, mts,
        'stat_type',
        constructed_filter,
        'stat_type'
    )

    constructed_filter = get_string_filter(
        filter_dict, mts,
        'stage',
        constructed_filter,
        'stage'
    )

    constructed_filter = get_int_filter(
        filter_dict, mts,
        'id',
        constructed_filter)
    
    constructed_filter = get_string_filter(filter_dict, im, 'name', constructed_filter, 'instrument_meta_name')

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
        filter_dict, rgs, 'name', constructed_filter, 'name')

    constructed_filter = get_float_filter(filter_dict, rgs, 'min_lat', constructed_filter)

    constructed_filter = get_float_filter(filter_dict, rgs, 'max_lat', constructed_filter)

    constructed_filter = get_float_filter(filter_dict, rgs, 'east_lon', constructed_filter)

    constructed_filter = get_float_filter(filter_dict, rgs, 'west_lon', constructed_filter)

    constructed_filter = get_int_filter(filter_dict, rgs, 'id', constructed_filter)

    return constructed_filter

def get_sat_meta_filter(filter_dict, constructed_filter):
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

    constructed_filter = get_string_filter(filter_dict, sm, 'name', constructed_filter, 'name')

    constructed_filter = get_int_filter(filter_dict, sm, 'sat_id', constructed_filter)

    constructed_filter = get_string_filter(filter_dict, sm, 'sat_name', constructed_filter, 'sat_name')

    constructed_filter = get_string_filter(filter_dict, sm, 'short_name', constructed_filter, 'short_name')

    return constructed_filter

def get_expt_record(body):

    # get experiment name
    expt_name = body.get('expt_name')
    datestr_format = body.get('datestr_format')
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
                raise ExptMetricsError(msg)
            record_cnt = records.shape[0]
        else:
            msg = f'Problems encountered requesting experiment data.'
            # create error return db_action_response
            raise ExptMetricsError(msg)
        if record_cnt <= 0:
            msg = 'Request for experiment record did not return a record'
            raise ExptMetricsError(msg)
        
    except Exception as err:
        msg = f'Problems encountered requesting experiment data. err - {err}'
        raise ExptMetricsError(msg)
    
    return records

def get_sat_meta_id_from_metric(metric):
    sat_meta_id = -1
    try:    
        sat_meta_name = metric.sat_meta_name
        sat_id = metric.sat_id
        sat_name = metric.sat_name
        sat_short_name = metric.sat_short_name
    except Exception as err:
        print(f'Required sat meta input value not found: {err}')
        return sat_meta_id
    
    if sat_meta_name is None and sat_id is None and sat_name is None and sat_short_name is None:
        return sat_meta_id
    
    sat_meta_request = {
        'name': 'sat_meta',
        'method': db_utils.HTTP_GET,
        'params': {
            'filters': {
                'name': {
                    'exact': sat_meta_name
                },
                'sat_name': {
                    'exact': sat_name
                },
                'short_name': {
                    'exact': sat_short_name
                },
                'sat_id': sat_id
            },
            'record_limit': 1
        }
    }

    print(f'sat_meta_request: {sat_meta_request}')

    smr = SatMetaRequest(sat_meta_request)

    results = smr.submit()
    print(f'results: {results}')

    record_cnt = 0
    try:
        if results.success is True:
            records = results.details.get('records')
            if records is None:
                msg = 'Request for sat meta record did not return a record'
                raise ExptMetricsError(msg)
            record_cnt = records.shape[0]
        else:
            msg = f'Problems encountered requesting sat meta data.'
            # create error return db_action_response
            raise ExptMetricsError(msg)
        if record_cnt <= 0:
            msg = 'Request for sat meta record did not return a record'
            raise ExptMetricsError(msg)
        
    except Exception as err:
        msg = f'Problems encountered requesting sat meta data. err - {err}'
        raise ExptMetricsError(msg) from err
        
    try:
        sat_meta_id = records[sm.id.name].iat[0]
    except Exception as err:
        error_msg = f'Problem finding sat meta id from record: {records} ' \
            f'- err: {err}'
        print(f'error_msg: {error_msg}')
        raise ExptMetricsError(error_msg) from err
    return sat_meta_id

def get_region_id_from_metric(metric):
    region_id = -1
    try:    
        region_name = metric.region_name
        region_min_lat = metric.region_min_lat
        region_max_lat = metric.region_max_lat
        region_east_lon = metric.region_east_lon
        region_west_lon = metric.region_west_lon
    except Exception as err:
        msg = f'Required region input value (name or lat and lon values) not found: {err}'
        raise ExptMetricsError(msg)
    
    if region_name is None and region_min_lat is None and region_max_lat is None and region_east_lon is None and region_west_lon is None:
        msg = 'No required region name or lat and lon values provided.'
        raise ExptMetricsError(msg)
    
    if region_min_lat is not None and region_max_lat is not None and region_east_lon is not None and region_west_lon is not None:
        region_request = {
            'name': 'region',
            'method': db_utils.HTTP_GET,
            'params': {
                'filter_type': 'by_data',
                'filters': {
                    'min_lat': region_min_lat,
                    'max_lat': region_max_lat,
                    'east_lon': region_east_lon,
                    'west_lon': region_west_lon
                },
                'record_limit': 1
            }
        }
    elif region_name is not None:
        region_request = {
            'name': 'region',
            'method': db_utils.HTTP_GET,
            'params': {
                'filter_type': 'by_name',
                'record_limit': 1
            },
            'body':{
                'regions': [region_name]
            }
        }
    else:
        raise ExptMetricsError('Was not provided either all four region bounds or a region name to search for. Region is required.')

    rr = RegionRequest(region_request)

    results = rr.submit()

    record_cnt = 0
    try:
        if results.success is True:
            records = results.details.get('records')
            if records is None:
                msg = 'Request for region record did not return a record. Region must be pre-registered.'
                raise ExptMetricsError(msg)
            record_cnt = records.shape[0]
        else:
            msg = f'Problems encountered requesting region data. Region is required.'
            raise ExptMetricsError(msg)
        if record_cnt <= 0:
            msg = 'Request for region record did not return a record. Region must be pre-registered.'
            raise ExptMetricsError(msg)
        
    except Exception as err:
        msg = f'Problems encountered requesting region data. err - {err}'
        raise ExptMetricsError(msg) from err
        
    try:
        region_id = records[rgs.id.name].iat[0]
    except Exception as err:
        error_msg = f'Problem finding region id from record: {records} ' \
            f'- err: {err}'
        print(f'error_msg: {error_msg}')
        raise ExptMetricsError(error_msg) from err
    
    if region_id < 0:
        raise ExptMetricsError("No region identified from input data.")
    return region_id

@dataclass
class ExptMetricRequest:
    request_dict: dict
    method: str = field(default_factory=str, init=False)
    params: dict = field(default_factory=dict, init=False)
    filters: dict = field(default_factory=dict, init=False)
    ordering: list = field(default_factory=dict, init=False)
    record_limit: int = field(default_factory=dict, init=False)
    body: dict = field(default_factory=dict, init=False)
    experiment: Experiment = field(init=False)
    expt_id: int = field(default_factory=int, init=False)
    response: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.method = db_utils.validate_method(self.request_dict.get('method'))
        self.params = self.request_dict.get('params')
        self.body = self.request_dict.get('body')
        self.filters = None
        self.ordering = None
        self.record_limit = None
        if self.params is not None:
            self.filters = self.params.get('filters')
            self.ordering = self.params.get('ordering')
            self.record_limit = self.params.get('record_limit')


    def submit(self):
        with stm.engine.connect() as connection:
            session = stm.Session(bind=connection)
            if self.method == db_utils.HTTP_GET:
                try:
                    return self.get_experiment_metrics(session)
                except Exception as err:
                    trcbk = traceback.format_exc()
                    error_msg = 'Failed to get experiment metric records -' \
                        f' trcbk: {trcbk}'
                    print(f'Submit GET error: {error_msg}')
                    return self.failed_request(error_msg)
                finally:
                    session.close()
            elif self.method == db_utils.HTTP_PUT:
                # becomes an update if record exists
                print(f'in PUT method')
                try:
                    return self.put_expt_metrics_data(session)
                except Exception as err:
                    trcbk = traceback.format_exc()
                    error_msg = 'Failed to insert experiment metric records -' \
                        f' trcbk: {trcbk}'
                    print(f'Submit PUT error: {error_msg}')
                    session.rollback()
                    return self.failed_request(error_msg)
                finally:
                    session.close()


    def failed_request(self, error_msg):
        return DbActionResponse(
            request=self.request_dict,
            success=False,
            message='Failed experiment metrics request.',
            details=None,
            errors=error_msg
        )


    def construct_filters(self, query):
        if not isinstance(self.filters, dict):
            msg = f'Filters must be of the form dict, filters: {type(self.filters)}'
            raise ExptMetricsError(msg)

        constructed_filter = {}

        # filter experiment metrics table for all matching experiments
        constructed_filter = get_experiments_filter(
            self.filters.get('experiment'), constructed_filter)

        # get only those records related to certain experiment
        constructed_filter = get_metric_types_filter(
            self.filters.get('metric_types'), constructed_filter)
        
        constructed_filter = get_regions_filter(
            self.filters.get('regions'), constructed_filter)
        
        constructed_filter = get_sat_meta_filter(self.filters.get('sat_meta'), constructed_filter)

        constructed_filter = get_time_filter(
            self.filters, ex_mt, 'time_valid', constructed_filter)

        constructed_filter = get_string_filter(
            self.filters,
            ex_mt,
            'elevation_unit',
            constructed_filter,
            'elevation_unit'
        )

        constructed_filter = get_float_filter(self.filters, ex_mt, 'forecast_hour', constructed_filter)

        constructed_filter = get_float_filter(self.filters, ex_mt, 'ensemble_member', constructed_filter)

        constructed_filter = get_int_filter(self.filters, ex_mt, 'id', constructed_filter)

        if len(constructed_filter) > 0:
            try:
                for key, value in constructed_filter.items():
                    print(f'adding filter: {value}')
                    query = query.filter(value)
            except Exception as err:
                msg = f'Problems adding filter to query - query: {query}, ' \
                    f'filter: {value}, err: {err}'
                raise ExptMetricsError(msg) from err

        return query


    def get_first_expt_id_from_df(self, record):
        try:
            self.expt_id = record[exp.id.name].iat[0]
        except Exception as err:
            error_msg = f'Problem finding experiment id from record: {record} ' \
                f'- err: {err}'
            print(f'error_msg: {error_msg}')
            raise ExptMetricsError(error_msg) 
        return self.expt_id
    

    def parse_metrics_data(self, metrics):
        if not isinstance(metrics, list):
            msg = f'\'metrics\' must be a list - was a \'{type(metrics)}\''
            raise ExptMetricsError(msg)
        
        # unique_regions = set()
        unique_metric_types = set()
        for metric in metrics:

            if not isinstance(metric, ExptMetricInputData):
                msg = 'Each metric must be a type ' \
                    f'\'{type(ExptMetricInputData)}\' was \'{metric}\''
                print(f'metric: {metric}, msg: {msg}')
                raise ExptMetricsError(msg)
            
            unique_metric_types.add(metric.name)

        metric_types = mt.get_all_metric_types()

        mt_df = metric_types.details.get('records')
        mt_df_nm_id = mt_df[['id', 'name']].copy()
        mt_df_dict = dict(zip(mt_df_nm_id.name, mt_df_nm_id.id))

        records = []
        for row in metrics:
            
            value = row.value
            region_id = get_region_id_from_metric(row)
            sat_meta_id = get_sat_meta_id_from_metric(row)
            sat_meta_input_id = sat_meta_id if sat_meta_id > 0 else None

            if math.isnan(value):
                value = None
            
            item = ex_mt(
                experiment_id=self.expt_id,
                metric_type_id=mt_df_dict[row.name],
                region_id=region_id,
                sat_meta_id=sat_meta_input_id,
                elevation=row.elevation,
                elevation_unit=row.elevation_unit,
                value=value,
                time_valid=row.time_valid,
                forecast_hour=row.forecast_hour,
                ensemble_member=row.ensemble_member
            )

            records.append(item)

        return records


    def get_expt_metrics_from_body(self, body):
        if not isinstance(body, dict):
            error_msg = 'The \'body\' key must be a type dict, was ' \
                f'{type(body)}'
            print(f'Metrics key not found: {error_msg}')
            raise ExptMetricsError(error_msg)

        metrics = body.get('metrics')
        parsed_metrics = self.parse_metrics_data(metrics)

        return parsed_metrics

    
    def put_expt_metrics_data(self, session):

        # we need to determine the primary key id from the experiment
        # all calls to this function must return a DbActionResponse object
        expt_record = get_expt_record(self.body)
        expt_id = self.get_first_expt_id_from_df(expt_record)
        records = self.get_expt_metrics_from_body(self.body)

        if len(records) > 0:
            # for record in records:
                # msg = f'record.experiment_id: {record.experiment_id}, '
                # msg += f'record.metric_type_id: {record.metric_type_id}, '
                # msg += f'record.region_id: {record.region_id}, '
                # msg += f'record.elevation: {record.elevation}, '
                # msg += f'record.elevation_unit: {record.elevation_unit}, '
                # msg += f'record.value: {record.value}, '
                # msg += f'record.time_valid: {record.time_valid}, '
                # msg += f'record.forecast_hour: {record.forecast_hour},'
                # msg += f'record.ensemble_member: {record.ensemble_member},'
                # msg += f'record.created_at: {record.created_at}'
                # print(f'record: {msg}')

            session.bulk_save_objects(records)
            session.commit()
        else:
            return self.failed_request('No expt metric records were discovered to be inserted')

        return DbActionResponse(
            request=self.request_dict,
            success=True,
            message="Attempt to insert expt metrics SUCCEEDED",
            details=records,
            errors=None
        )

    
    def get_experiment_metrics(self, session):
        # set basic query
        q = session.query(
            ex_mt
        ).join(
            exp, ex_mt.experiment
        ).join(
            rgs, ex_mt.region
        ).outerjoin(
            sm, ex_mt.sat_meta
        ).join(
            mts, ex_mt.metric_type
        ).outerjoin(
            im, mts.instrument_meta
        )

        # add filters
        q = self.construct_filters(q)

        # # add column ordering
        column_ordering = db_utils.build_column_ordering(ex_mt, self.ordering)
        if column_ordering is not None and len(column_ordering) > 0:
            for ordering_item in column_ordering:
                q = q.order_by(ordering_item)

        metrics = q.all()

        print(f'len(metrics): {len(metrics)}')
        parsed_metrics = []
        for metric in metrics:
            #handle potential nulls from outer joins
            sat_meta_id=None
            sat_meta_name=None
            sat_id=None
            sat_name=None
            sat_short_name=None
            metric_instrument_name=None
            metric_instrument_num_channels=None
            if metric.sat_meta is not None:
                sat_meta_id=metric.sat_meta.id
                sat_meta_name=metric.sat_meta.name
                sat_id=metric.sat_meta.sat_id
                sat_name=metric.sat_meta.sat_name
                sat_short_name=metric.sat_meta.short_name
            if metric.metric_type.instrument_meta is not None:
                metric_instrument_name=metric.metric_type.instrument_meta.name
                metric_instrument_num_channels=metric.metric_type.instrument_meta.num_channels

            record = ExptMetricsData(
                id=metric.id,
                name=metric.metric_type.name,
                elevation=metric.elevation,
                elevation_unit=metric.elevation_unit,
                value=metric.value,
                time_valid=metric.time_valid,
                forecast_hour=metric.forecast_hour,
                ensemble_member=metric.ensemble_member,
                expt_id=metric.experiment.id,
                expt_name=metric.experiment.name,
                wallclock_start=metric.experiment.wallclock_start,
                metric_id=metric.metric_type.id,
                metric_long_name=metric.metric_type.long_name,
                metric_type=metric.metric_type.measurement_type,
                metric_unit=metric.metric_type.measurement_units,
                metric_stat_type=metric.metric_type.stat_type,
                metric_stage=metric.metric_type.stage,
                metric_instrument_meta_id=metric.metric_type.instrument_meta_id,
                metric_instrument_name=metric_instrument_name,
                metric_instrument_num_channels=metric_instrument_num_channels,
                metric_obs_platform=metric.metric_type.obs_platform,
                region_id=metric.region.id,
                region_name=metric.region.name,
                region_min_lat=metric.region.min_lat,
                region_max_lat=metric.region.max_lat,
                region_east_lon=metric.region.east_lon,
                region_west_lon=metric.region.west_lon,
                sat_meta_id=sat_meta_id,
                sat_meta_name=sat_meta_name,
                sat_id=sat_id,
                sat_name=sat_name,
                sat_short_name=sat_short_name,
                created_at=metric.created_at
            )
            parsed_metrics.append(record)
        
        try:
            metrics_df = DataFrame(
                parsed_metrics,
                columns=ExptMetricsData._fields
            )
        except Exception as err:
            trcbk = traceback.format_exc()
            msg = f'Problem casting exeriment metrics query output into pandas ' \
                f'DataFrame - err: {trcbk}'
            raise TypeError(msg) from err
        
        unique_metrics = self.remove_metric_duplicates(metrics_df)

        results = DataFrame()   
        error_msg = None
        record_count = 0
        try:
            if len(parsed_metrics) > 0:
                results = unique_metrics
            
        except Exception as err:
            message = 'Request for experiment metric records FAILED'
            trcbk = traceback.format_exc()
            error_msg = f'Failed to get any experiment metrics - err: {trcbk}'
            print(f'error_msg: {error_msg}')
        else:
            message = 'Request for experiment metrics SUCCEEDED'
            record_count = len(results.index)
        
        details = {}
        details['record_count'] = record_count

        if record_count > 0:
            details['records'] = results

        response = DbActionResponse(
            self.request_dict,
            (error_msg is None),
            message,
            details,
            error_msg
        )

        print(f'response: {response}')

        return response


    def remove_metric_duplicates(self, m_df):
        
        start_records = m_df.shape[0]
        print(f'starting records: {start_records}')

        try:

            uf = m_df.sort_values(
                'created_at'
            ).drop_duplicates(
                [
                    'name',
                    'elevation',
                    'elevation_unit',
                    'time_valid',
                    'forecast_hour',
                    'ensemble_member',
                    'expt_id',
                    'metric_id',
                    'region_id',
                    'sat_meta_id'
                ],
                keep='last'
            )

        except Exception as err:
            trcbk = traceback.format_exc()
            msg = f'Failed to drop duplicates - err: {trcbk}'
            raise ValueError(msg)
        
        end_records = uf.shape[0]
        print(f'ending records: {end_records}')
        return uf
