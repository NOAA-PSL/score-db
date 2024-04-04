"""
Copyright NOAA 2024
All rights reserved.

Collection of methods to facilitate interactions with the array metric types table. 
"""

from collections import namedtuple
import copy
from dataclasses import dataclass, field
from datetime import datetime
import json
import pprint
from db_action_response import DbActionResponse
import score_table_models as stm
from score_table_models import ArrayMetricType as amt
from score_table_models import SatMeta as sm
from sat_meta import SatMetaRequest
import time_utils
import db_utils
import traceback

from pandas import DataFrame 
import sqlalchemy as db
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.inspection import inspect
from sqlalchemy import and_, or_, not_
from sqlalchemy import asc, desc
from sqlalchemy.sql import func

ArrayMetricTypeInputData = namedtuple(
    'ArrayMetricTypeInputData',
    [
        'name',
        'long_name',
        'obs_platform',
        'measurement_type',
        'measurement_units',
        'stat_type',
        'array_coord_labels',
        'array_coord_units',
        'array_index_values',
        'array_dimensions',
        'description',
    ],
)

ArrayMetricTypeData = namedtuple(
    'ArrayMetricTypeData',
    [
        'id',
        'name',
        'long_name',
        'obs_platform',
        'measurement_type',
        'measurement_units',
        'stat_type',
        'array_coord_labels',
        'array_coord_units',
        'array_index_values',
        'array_dimensions',
        'description',
        'sat_meta_id',
        'sat_meta_name',
        'sat_id',
        'sat_name',
        'sensor',
        'channel',
        'scan_angle'
    ]
)

class ArrayMetricTypeError(Exception):
    def __init__(self, m):
        self.message = m
    def __str__(self):
        return self.message

@dataclass
class ArrayMetricType:
    '''array metric type object for storing type data'''
    name: str
    long_name: str
    obs_platform: str
    measurement_type: str
    measurement_units: str
    stat_type: str
    array_coord_labels: list
    array_coord_units: list
    array_index_values: list
    array_dimensions: list
    description: dict
    array_metric_type_data: ArrayMetricTypeInputData = field(init=False)

    def __post_init__(self):
        self.array_metric_type_data = ArrayMetricTypeInputData(
            self.name,
            self.long_name,
            self.obs_platform,
            self.measurement_type,
            self.measurement_units,
            self.stat_type,
            self.array_coord_labels,
            self.array_coord_units,
            self.array_index_values,
            self.array_dimensions,
            self.description
        )

    def __repr__(self):
        return f'array_metric_type_data: {self.array_metric_type_data}'
    
    def get_array_metric_type_data(self):
        return self.array_metric_type_data
    
def get_array_metric_type_from_body(body):
    if not isinstance(body, dict):
        msg = 'The \'body\' key must be a type dict, was ' \
            f'{type(body)}'
        raise TypeError(msg)
    
    try:
        description = json.loads(body.get('description'))
    except Exception as err:
        msg = 'Error loading \'description\', must be valid JSON - err: {err}'
        raise ValueError(msg) from err
    
    array_metric_type = ArrayMetricType(
        name=body.get('name'),
        long_name=body.get('long_name'),
        obs_platform=body.get('obs_platform'),
        measurement_type=body.get('measurement_type'),
        measurement_units=body.get('measurement_units'),
        stat_type=body.get('stat_type'),
        array_coord_labels=body.get('array_coord_labels'),
        array_coord_units=body.get('array_coord_units'),
        array_index_values=body.get('array_index_values'),
        array_dimensions=body.get('array_dimensions'),
        description=description
    )

    return array_metric_type


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


def construct_filters(filters):
    constructed_filter = {}

    constructed_filter = get_string_filter(filters, amt, 'name', constructed_filter, 'name')
    
    constructed_filter = get_string_filter(filters, amt, 'long_name', constructed_filter, 'long_name')
    
    constructed_filter = get_string_filter(filters, amt, 'obs_platform', constructed_filter, 'obs_platform')

    constructed_filter = get_string_filter(filters, amt, 'measurement_type', constructed_filter, 'measurement_type')

    constructed_filter = get_string_filter(filters, amt, 'measurement_units', constructed_filter, 'measurement_units')

    constructed_filter = get_string_filter(filters, amt, 'stat_type', constructed_filter, 'stat_type')
    
    constructed_filter = get_string_filter(filters, sm, 'name', constructed_filter, 'sat_meta_name')
    
    return constructed_filter

def get_all_array_metric_types():
    request_dict = {
        'name': 'array_metric_type',
        'method': 'GET'
    }

    amtr = ArrayMetricTypeRequest(request_dict)
    return amtr.submit()

def get_sat_meta_id(body):
    sat_meta_id = -1
    try:    
        sat_meta_name = body.get('sat_meta_name')
        sat_id = body.get('sat_id')
        sat_name = body.get('sat_name')
        sat_sensor = body.get('sat_sensor')
        sat_channel = body.get('sat_channel')
    except KeyError as err:
        print(f'Required sat meta input value not found: {err}')
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
                'sensor': {
                    'exact': sat_sensor
                },
                'sat_id': sat_id,
                'channel':{
                    'exact': sat_channel
                }
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
                raise ArrayMetricTypeError(msg)
            record_cnt = records.shape[0]
        else:
            msg = f'Problems encountered requesting sat meta data.'
            # create error return db_action_response
            raise ArrayMetricTypeError(msg)
        if record_cnt <= 0:
            msg = 'Request for sat meta record did not return a record'
            raise ArrayMetricTypeError(msg)
        
    except Exception as err:
        msg = f'Problems encountered requesting sat meta data. err - {err}'
        raise ArrayMetricTypeError(msg)
        
    try:
        sat_meta_id = records[sm.id.name].iat[0]
    except Exception as err:
        error_msg = f'Problem finding sat meta id from record: {records} ' \
            f'- err: {err}'
        print(f'error_msg: {error_msg}')
        raise ArrayMetricTypeError(error_msg) 
    return sat_meta_id

@dataclass
class ArrayMetricTypeRequest:
    request_dict: dict
    method: str = field(default_factory=str, init=False)
    params: dict = field(default_factory=dict, init=False)
    filters: dict = field(default_factory=dict, init=False)
    ordering: list = field(default_factory=list, init=False)
    record_limit: int = field(default_factory=int, init=False)
    body: dict = field(default_factory=dict, init=False)
    array_metric_type: ArrayMetricType = field(init=False)
    array_metric_type_data: namedtuple = field(init=False)
    sat_meta_id: int = field(default_factory=int, init=False)
    response: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.method = db_utils.validate_method(self.request_dict.get('method'))
        self.params = self.request_dict.get('params')

        self.body = self.request_dict.get('body')
        if self.method == db_utils.HTTP_PUT:
            try:
                self.array_metric_type = get_array_metric_type_from_body(self.body)
                self.array_metric_type_data = self.array_metric_type.get_array_metric_type_data()
                self.sat_meta_id = get_sat_meta_id(self.body)
            except Exception as err:
                error_msg = 'Failed to get array metric type information to insert -' \
                    f' err: {err}'
                print(f'Submit PUT error: {error_msg}')
                return self.failed_request(error_msg)
        else:
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
            message='Failed array metric type request.',
            details=None,
            errors=error_msg
        )
    
    def submit(self):
        if self.method == db_utils.HTTP_GET:
            return self.get_array_metric_types()
        elif self.method == db_utils.HTTP_PUT:
            try:
                return self.put_array_metric_type()
            except Exception as err:
                error_msg = 'Failed to insert array metric type record -' \
                    f' err: {err}'
                print(f'Submit PUT error: {error_msg}')
                return self.failed_request(error_msg)
            
    def put_array_metric_type(self):
        session = stm.get_session()

        sat_meta_id = self.sat_meta_id if self.sat_meta_id > 0 else None

        insert_stmt = insert(amt).values(
            name=self.array_metric_type_data.name,
            long_name=self.array_metric_type_data.long_name, 
            obs_platform=self.array_metric_type_data.obs_platform,
            sat_meta_id=sat_meta_id, 
            measurement_type=self.array_metric_type_data.measurement_type,
            measurement_units=self.array_metric_type_data.measurement_units,
            stat_type=self.array_metric_type_data.stat_type,
            array_coord_labels=self.array_metric_type_data.array_coord_labels,
            array_coord_units=self.array_metric_type_data.array_coord_units,
            array_index_values=self.array_metric_type_data.array_index_values,
            array_dimensions=self.array_metric_type_data.array_dimensions,
            description=self.array_metric_type_data.description,
            created_at=datetime.utcnow(),
            updated_at=None
        ).returning(amt)
        print(f'insert_stmt: {insert_stmt}')

        time_now = datetime.utcnow()

        do_update_stmt = insert_stmt.on_conflict_do_update(
            constraint='unique_array_metric_type',
            set_=dict(
                long_name=self.array_metric_type_data.long_name, 
                array_coord_labels=self.array_metric_type_data.array_coord_labels,
                array_coord_units=self.array_metric_type_data.array_coord_units,
                array_index_values=self.array_metric_type_data.array_index_values,
                array_dimensions=self.array_metric_type_data.array_dimensions,
                description=self.array_metric_type_data.description,
                updated_at=time_now
            )
        )

        print(f'do_update_stmt: {do_update_stmt}')

        try:
            result = session.execute(do_update_stmt)
            session.flush()
            result_row = result.fetchone()
            action = db_utils.INSERT
            if result_row.updated_at is not None:
                action = db_utils.UPDATE

            session.commit()
            session.close()
        except Exception as err:
            message = f'Attempt to INSERT/UPDATE array metric type record FAILED'
            error_msg = f'Failed to insert/update record - err: {err}'
            print(f'error_msg: {error_msg}')
            session.close()
        else:
            message = f'Attempt to {action} array metric type record SUCCEEDED'
            error_msg = None
        
        results = {}
        if result_row is not None:
            results['action'] = action
            results['data'] = [result_row._mapping]
            results['id'] = result_row.id

        response = DbActionResponse(
            self.request_dict,
            (error_msg is None),
            message,
            results,
            error_msg
        )

        print(f'response: {response}')
        return response

    def get_array_metric_types(self):
        session = stm.get_session()

        q = session.query(
            amt
        ).join(
            sm, amt.sat_meta
        )

        print('Before adding filters to array metric types request########################')
        if self.filters is not None and len(self.filters) > 0:
            for key, value in self.filters.items():
                q = q.filter(value)
        
        print('After adding filters to array metric types request########################')
        
        # add column ordering
        column_ordering = db_utils.build_column_ordering(amt, self.ordering)
        if column_ordering is not None and len(column_ordering) > 0:
            for ordering_item in column_ordering:
                q = q.order_by(ordering_item)

        # limit number of returned records
        if self.record_limit is not None and self.record_limit > 0:
            q = q.limit(self.record_limit)

        array_metric_types = q.all()

        parsed_types = []
        for metric_type in array_metric_types:
            record = ArrayMetricTypeData(
                id=metric_type.id,
                name=metric_type.name,
                long_name=metric_type.long_name,
                obs_platform=metric_type.obs_platform,
                measurement_type=metric_type.measurement_type,
                measurement_units=metric_type.measurement_units,
                stat_type=metric_type.stat_type,
                array_coord_labels=metric_type.array_coord_labels,
                array_coord_units=metric_type.array_coord_units,
                array_index_values=metric_type.array_index_values,
                array_dimensions=metric_type.array_dimensions,
                description=metric_type.description,
                sat_meta_id=metric_type.sat_meta.id,
                sat_meta_name=metric_type.sat_meta.name,
                sat_id=metric_type.sat_meta.sat_id,
                sat_name=metric_type.sat_meta.sat_name,
                sensor=metric_type.sat_meta.sensor,
                channel=metric_type.sat_meta.channel,
                scan_angle=metric_type.sat_meta.scan_angle
            )
            parsed_types.append(record)

        try:
            arr_metric_types_df = DataFrame(
                parsed_types,
                columns=ArrayMetricTypeData._fields
            )
        except Exception as err:
            trcbk = traceback.format_exc()
            msg = f'Problem casting array metric type query output into pandas ' \
                f'DataFrame - err: {trcbk}'
            raise TypeError(msg) from err

        results = DataFrame()
        error_msg = None
        record_count = 0
        try:
            if len(parsed_types) > 0:
                results = arr_metric_types_df
            
        except Exception as err:
            message = 'Request for array metric type records FAILED'
            error_msg = f'Failed to get array metric type records - err: {err}'
        else:
            message = 'Request for array metric type records SUCCEEDED'
            for idx, row in results.iterrows():
                print(f'idx: {idx}, row: {row}')
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

        session.close()
        return response
