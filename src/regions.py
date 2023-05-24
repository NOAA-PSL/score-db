"""
Copyright 2022 NOAA
All rights reserved.

Collection of methods and classes to facilitate insertion and selection
of records into/from the 'regions' table.  The region table includes the
following columns ['name', 'min_lat', 'max_lat', 'min_lon', 'max_lon', 'created_at', 'updated_at'] and each
row's id serves as a foreign key to the 'expt_metrics' table.  A unique
region consists of a combination of the name and the bounds values.
Multiple regions with the same 'name' value are allowed as long as the
'bounds' values are different.

Each experiment metric is associated with a region (through the region's
foreign key 'id') in order to limit duplicated data.


"""
from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from db_action_response import DbActionResponse
import score_table_models as stm
from score_table_models import Region as rg
import db_utils

from pandas import DataFrame
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.inspection import inspect

PARAM_FILTER_TYPE = 'filter_type'

FILTER__NONE = 'none'
FILTER__BY_REGION_NAME = 'by_name'
FILTER__BY_REGION_DATA = 'by_data'

VALID_FILTER_TYPES = [
    FILTER__NONE, FILTER__BY_REGION_NAME, FILTER__BY_REGION_DATA]

EQUATORIAL = {'name': 'equatorial', 'min_lat': -5.0, 'max_lat': 5.0, 'min_lon': 0.0, 'max_lon': 360.0}
GLOBAL = {'name': 'global', 'min_lat': -90.0, 'max_lat': 90.0, 'min_lon': 0.0, 'max_lon': 360.0}
NORTH_MIDLAT = {'name': 'north_midlatitudes', 'min_lat': 20.0, 'max_lat': 60.0, 'min_lon': 0.0, 'max_lon': 360.0}
TROPICS = {'name': 'tropics', 'min_lat': -20.0, 'max_lat': 20.0, 'min_lon': 0.0, 'max_lon': 360.0}
SOUTH_MIDLAT = {'name': 'south_midlatitudes', 'min_lat': -60.0, 'max_lat': -20.0, 'min_lon': 0.0, 'max_lon': 360.0}
TEST_SOUTH_HEMIS = {'name': 'test_south_hemis', 'min_lat': -50.0, 'max_lat': -35.0, 'min_lon': 0.0, 'max_lon': 360.0}

RegionData = namedtuple(
    'RegionData',
    [
        'name',
        'min_lat',
        'max_lat',
        'min_lon',
        'max_lon'
    ],
)

class RegionError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

@dataclass
class Region:
    ''' region object storing region name and min/max latitude/longitude bounds '''
    name: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    def __post_init__(self):
        if not isinstance(self.name, str):
            msg = f'name must be a string - name {self.name}'
            raise TypeError(msg)
        #latitude checks
        if (not isinstance(self.min_lat, float) or
            not isinstance(self.max_lat, float)):
            msg = f'min and max lat must be floats - min lat: {self.min_lat}' \
                f', max lat: {self.max_lat}'
            raise ValueError(msg)
        if self.min_lat > self.max_lat:
            msg = f'min_lat must be less than max_lat - ' \
                f'min_lat: {self.min_lat}, max_lat: {self.max_lat}'
            raise ValueError(msg)
        if self.max_lat < self.min_lat:
            msg = f'max_lat must be greater than min_lat - min_lat: {self.min_lat}, '\
                f'max_lat: {self.max_lat}'
            raise ValueError(msg)
        if abs(self.min_lat) > 90 or abs(self.max_lat) > 90:
            msg = f'min_lat or max_lat is out of allowed range, must be greater' \
                f' than -90 and less than 90 - min_lat: {self.min_lat}, ' \
                f'max_lat: {self.max_lat}'
            raise ValueError(msg)
        #longitude checks
        if (not isinstance(self.min_lon, float) or
            not isinstance(self.max_lon, float)):
            msg = f'min and max lon must be floats - min lon: {self.min_lon}' \
                f', max lon: {self.max_lon}'
            raise ValueError(msg)
        #convert from -180 to 0 to 0 to 360 if necessary 
        if self.min_lon < 0:
            self.min_lon = 360 + self.min_lon
        if self.max_lon < 0:
            self.max_lon = 360 + self.max_lon
        #check values     
        if self.min_lon > self.max_lon:
            msg = f'min_lon must be less than max_lon - ' \
                f'min_lon: {self.min_lon}, max_lon: {self.max_lon}'
            raise ValueError(msg)
        if self.max_lon < self.min_lon:
            msg = f'max_lon must be greater than min_lon - min_lon: {self.min_lon}, '\
                f'max_lon: {self.max_lon}'
            raise ValueError(msg)
        if self.min_lon < 0 or self.max_lon > 360:
            msg = f'min_lon or max_lon is out of allowed range, must be greater' \
                f' than 0 and less than 360 - min_lon: {self.min_lon}, ' \
                f'max_lon: {self.max_lon}'
            raise ValueError(msg)

    
    def get_region_data(self):
        return RegionData(self.name, self.min_lat, self.max_lat, self.min_lon, self.max_lon)

def validate_list_of_regions(regions):
    if not isinstance(regions, list):
        raise TypeError(f'Must be list of Regions, was {type(regions)}')
    
    unique_regions = set()
    try:
        for r in regions:
            validated_region = Region(r.get('name'), r.get('min_lat'), r.get('max_lat'), 
                                      r.get('min_lon'), r.get('max_lon'))
            unique_regions.add(validated_region.get_region_data())
    except Exception as err:
        msg = f'problem parsing region data, regions: {regions}, err: {err}'
        raise TypeError(msg) from err
    
    return list(unique_regions)

def validate_list_of_strings(values):
    if not isinstance(values, list):
        raise TypeError(f'Must be list of strings, was {type(values)}')
    if not all(isinstance(elem, str) for elem in values):
        raise TypeError(f'Not all members are strings - {values}')
    
    unique_string_list = set()
    for value in values:
        unique_string_list.add(value)
    
    return list(unique_string_list)


def validate_body(method, body, filter_type=None):
    
    if not isinstance(body, dict):
        msg = f'Request body must be a dict type, was: {type(body)}'
        raise TypeError(msg)
    
    region_names = None
    regions = None
    
    if method == db_utils.HTTP_GET:
        if filter_type is None:
            raise ValueError('\'filter_type\' param must be specified.')
        if filter_type == FILTER__BY_REGION_NAME:
            region_names = validate_list_of_strings(body.get('regions')) 
        
    elif method == db_utils.HTTP_PUT:
        regions = validate_list_of_regions(body.get('regions'))
        region_names = [x.name for x in regions]
    
    else:
        raise ValueError(f'Invalid method, must be one of {db_utils.VALID_METHODS}')

    print(f'region_names: {region_names}, regions: {regions}')
    return [region_names, regions]


def get_filter_type(params):
    filter_type = params.get(PARAM_FILTER_TYPE)
    if filter_type is None:
        return FILTER__NONE
    elif filter_type not in VALID_FILTER_TYPES:
        raise ValueError(f'Invalid filter_type ({filter_type}). ' \
            f'Must be one of [{VALID_FILTER_TYPES}]')
    return filter_type

#used in expt metrics to check for existing regions / should get removed
def get_regions_from_name_list(region_names):
    request_dict = {
        'name': 'region',
        'method': 'GET',
        'params': {'filter_type': 'by_name'},
        'body': {
            'regions': region_names
        }
    }

    rr = RegionRequest(request_dict)
    return rr.submit()
    
def get_string_filter(filters, cls, key, constructed_filter):
        if not isinstance(filters, dict):
            msg = f'Invalid type for filters, must be \'dict\', was ' \
                f'type: {type(filters)}'
            raise TypeError(msg)

        print(f'Column \'{key}\' is of type {type(getattr(cls, key).type)}.')
        string_flt = filters.get(key)

        if string_flt is None:
            print(f'No \'{key}\' filter detected')
            return constructed_filter

        like_filter = string_flt.get('like')
        # prefer like search over exact match if both exist
        if like_filter is not None:
            constructed_filter[key] = (getattr(cls, key).like(like_filter))
            return constructed_filter

        exact_match_filter = string_flt.get('exact')
        if exact_match_filter is not None:
            constructed_filter[key] = (getattr(cls, key) == exact_match_filter)

        return constructed_filter

def construct_filters(filters):
        constructed_filter = {}

        constructed_filter = get_string_filter(filters, rg, 'name', constructed_filter)

        constructed_filter = get_string_filter(filters, rg, 'min_lat', constructed_filter)

        constructed_filter = get_string_filter(filters, rg, 'max_lat', constructed_filter)

        constructed_filter = get_string_filter(filters, rg, 'min_lon', constructed_filter)

        constructed_filter = get_string_filter(filters, rg, 'max_lon', constructed_filter)

        return constructed_filter

@dataclass
class RegionRequest:
    request_dict: dict
    method: str = field(default_factory=str, init=False)
    params: dict = field(default_factory=dict, init=False)
    filter_type: str = field(default_factory=str, init=False)
    body: dict = field(default_factory=dict, init=False)
    regions: list = field(default_factory=list, init=False)
    region_names: list = field(default_factory=list, init=False)
    response: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.method = db_utils.validate_method(self.request_dict.get('method'))
        self.params = self.request_dict.get('params', {})
        self.filter_type = get_filter_type(self.params)
        self.body = self.request_dict.get('body')
        [self.region_names, self.regions] = validate_body(
            self.method, self.body, self.filter_type)

    def submit(self):
        if self.method == db_utils.HTTP_GET:
            error_msg = None
            message = None
            matched_json = None
            try:
                if self.filter_type == FILTER__NONE:
                    matched_records = self.get_all_regions()
                elif self.filter_type == FILTER__BY_REGION_NAME:
                    matched_records = self.get_regions_by_name()
                else: #Filter by Region Data
                    matched_records = self.get_regions_by_data()
                message = f'Request returned {len(matched_records)} record/s'
                matched_json = matched_records.to_json(orient = 'records')
            except Exception as err:
                error_msg = f'Problems encountered requesting regions - {err}'
            print(f'matched_records: {matched_records}')
            response = DbActionResponse(
                self.request_dict,
                (error_msg is None),
                message,
                {
                    'matched_records': matched_json,
                    'records': matched_records
                },
                error_msg
            )
            print(f'response: {response}')
            return response
        elif self.method == db_utils.HTTP_PUT:
            try:
                return self.put_regions()
            except Exception as err:
                error_msg = f'Failed to put region record - err: {err}'
                print(f'Submit PUT error: {error_msg}')
                return self.failed_request(error_msg)

    #get regions filtered by name 
    def get_regions_by_name(self):
        session = stm.get_session()
        try:
            existing_regions = session.query(
                rg.id,
                rg.name,
                rg.min_lat,
                rg.max_lat,
                rg.min_lon,
                rg.max_lon,
                rg.created_at,
                rg.updated_at
            ).select_from(
                rg
            ).filter(
                rg.name.in_(self.region_names)
            ).all()
        except Exception as err:
            msg = f'Problem requesting region set - err: {err}'
            print(msg)
            return DataFrame()

        session.close()
        if len(existing_regions) == 0:
            return DataFrame()

        return DataFrame(existing_regions, columns = existing_regions[0]._fields)

    #get all regions in database
    def get_all_regions(self):
        session = stm.get_session()
        try:
            existing_regions = session.query(
                rg.id,
                rg.name,
                rg.min_lat,
                rg.max_lat,
                rg.min_lon,
                rg.max_lon,
                rg.created_at,
                rg.updated_at
            ).select_from(
                rg
            ).all()
        except Exception as err:
            msg = f'Problem requesting region set - err: {err}'
            print(msg)
            return DataFrame()

        session.close()
        if len(existing_regions) == 0:
            return DataFrame()

        return DataFrame(existing_regions, columns = existing_regions[0]._fields)
    
    #get regions based on filters on user provided restrictions on values 
    def get_regions_by_data(self):
        if self.params.len() < 0:
            msg = f'To filter regions by data, there must be a params which includes filters for the data'
            raise RegionError(msg)
        
        filters = self.request_dict.params.get('filters')
        if not isinstance(filters, dict):
            msg = f'Filters must be in teh form dict, filters: {type(filters)}'
            raise RegionError(msg)
        
        session = stm.get_session()

        q = session.query(
            rg.id,
            rg.name,
            rg.min_lat,
            rg.max_lat,
            rg.min_lon,
            rg.max_lon,
            rg.created_at,
            rg.updated_at
        ).select_from(
            rg
        )

        print('Before addinng filters to region request###')
        for key, value in filters.items():
            q = q.filter(value)
        print('After adding regions filter')

        regions = q.all()
        session.close()
 
        results = DataFrame()
        if len(regions) > 0:
            results = DataFrame(regions, columns = regions[0]._fields)
        return results
    
    def put_regions(self):
        session = stm.get_session()
        all_results = []
        error_msgs = None
        for region in self.regions:
            time_now = datetime.utcnow()

            insert_stmt = insert(rg).values(
                name=region.name, 
                min_lat=region.min_lat, 
                max_lat=region.max_lat,
                min_lon=region.min_lon,
                max_lon=region.max_lon,
                created_at=time_now,
                update_at=None
            ).returning(rg)

            do_update_stmt = insert_stmt.on_conflict_do_update(
                constraint='unique_region',
                set=dict(
                    name=region.name,
                    min_lat=region.min_lat,
                    max_lat=region.max_lat,
                    min_lon=region.min_lon,
                    max_lon=region.max_lon,
                    updated_at=time_now
                )
            )

            try:
                result =session.execute(do_update_stmt)
                session.flush()
                result_row = result.fetchone()
                action = db_utils.INSERT
                if result_row.updated_at is not None:
                    action = db_utils.UPDATE
                session.commit()
                session.close()
            except Exception as err:
                message = f'Attempt to {action} region record FAILED'
                error_msg = f'Failed to insert/update record -err: {err}'
                print(f'error_msg: {error_msg}')
            else:
                message = f'Attempt to {action} region record SUCCEEDED'
                error_msg = None
            
            results = {}
            if result_row is not None:
                results['region_name'] = region.name
                results['action'] = action
                results['data'] = [result_row._mapping]
                results['id'] = result_row.index
            
            if results.len() > 0:
                all_results.add(results)

            if error_msg is not None:
                error_msgs += error_msg + "\n"

        
        response = DbActionResponse(
            self.request_dict,
            (error_msgs is None),
            message,
            all_results,
            error_msg
        )
        print(f'response: {response}')
        return response   

            
