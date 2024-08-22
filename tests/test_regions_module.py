"""
Copyright 2022 NOAA
All rights reserved.

Unit tests for io_utils

"""
import os
import pathlib
import pytest

import score_db.score_table_models as scr_models
from score_db.score_table_models import Region as regions_table
import score_db.regions as rgs
from score_db.regions import RegionData, Region, RegionRequest
from score_db import db_utils

from score_db.score_db_base import handle_request

#test regions
EQUATORIAL = {'name': 'equatorial', 'min_lat': -5.0, 'max_lat': 5.0, 'east_lon': 0.0, 'west_lon': 360.0}
GLOBAL = {'name': 'global', 'min_lat': -90.0, 'max_lat': 90.0, 'east_lon': 0.0, 'west_lon': 360.0}
NORTH_MIDLAT = {'name': 'north_midlatitudes', 'min_lat': 20.0, 'max_lat': 60.0, 'east_lon': 0.0, 'west_lon': 360.0}
TROPICS = {'name': 'tropics', 'min_lat': -20.0, 'max_lat': 20.0, 'east_lon': 0.0, 'west_lon': 360.0}
SOUTH_MIDLAT = {'name': 'south_midlatitudes', 'min_lat': -60.0, 'max_lat': -20.0, 'east_lon': 0.0, 'west_lon': 360.0}

def test_validate_list_of_strings():
    with pytest.raises(TypeError):
        rgs.validate_list_of_strings({})

    with pytest.raises(TypeError):
        rgs.validate_list_of_strings(None)

    with pytest.raises(TypeError):
        rgs.validate_list_of_strings('dude')

    with pytest.raises(TypeError):
        rgs.validate_list_of_strings([1, 5, 6])

    region_list = ['foo', 'bar', 'foo']
    output_list = rgs.validate_list_of_strings(region_list)
    for output in output_list:
        assert output_list.count(output) == 1


def test_validate_list_of_regions():
    with pytest.raises(TypeError):
        rgs.validate_list_of_regions(None)

    with pytest.raises(TypeError):
        rgs.validate_list_of_regions({})

    with pytest.raises(TypeError):
        rgs.validate_list_of_regions('foo')

    with pytest.raises(TypeError):
        rgs.validate_list_of_regions(1)

    region_list = [EQUATORIAL, GLOBAL, SOUTH_MIDLAT, GLOBAL]
    validated_regions = rgs.validate_list_of_regions(region_list)
    print(f'validated_regions: {validated_regions}')
    for region in validated_regions:
        assert validated_regions.count(region) == 1
        assert isinstance(region, RegionData)


def test_validate_body():
    with pytest.raises(TypeError):
        rgs.validate_body(db_utils.HTTP_GET, None)

    with pytest.raises(TypeError):
        rgs.validate_body(db_utils.HTTP_GET, None)

    with pytest.raises(TypeError):
        rgs.validate_body(db_utils.HTTP_GET, [])

    with pytest.raises(TypeError):
        rgs.validate_body(db_utils.HTTP_GET, 'foo')

    with pytest.raises(TypeError):
        rgs.validate_body(db_utils.HTTP_GET, 1)
    

    body = {'regions': {}}
    with pytest.raises(TypeError):
        rgs.validate_body(db_utils.HTTP_GET, body, rgs.FILTER__BY_REGION_NAME)
    
    body = {'regions': [1, 2, 9]}
    with pytest.raises(TypeError):
        rgs.validate_body(db_utils.HTTP_GET, body, rgs.FILTER__BY_REGION_NAME)

    body = {'regions': ['foo', 'bar', 'foo']}
    [region_names, regions] = rgs.validate_body(db_utils.HTTP_GET, body, rgs.FILTER__BY_REGION_NAME)
    for name in region_names:
        assert region_names.count(name) == 1
    
    assert regions is None

    body = {'regions': [GLOBAL, EQUATORIAL, GLOBAL]}
    [region_names, regions] = rgs.validate_body(db_utils.HTTP_PUT, body)
    for name in region_names:
        assert region_names.count(name) == 1
        print(f'name: {name}')
    
    for region in regions:
        assert regions.count(region) == 1
        assert isinstance(region, RegionData)

def test_initialize_region_request_prep():
    request_dict = {
        'db_request_name': 'region',
        'method': 'PUT',
        'body': {
            'regions': [
                GLOBAL,
                EQUATORIAL,
                NORTH_MIDLAT,
                SOUTH_MIDLAT,
                TROPICS,
                GLOBAL
            ]
        }
    }

    rr = RegionRequest(request_dict)
    print(f'rr_prep: {rr}')

    for name in rr.region_names:
        print(f'region: {name}')

def test_request_put_regions():
    request_dict = {
        'db_request_name': 'region',
        'method': db_utils.HTTP_PUT,
        'body': {
            'regions': [
                GLOBAL,
                EQUATORIAL,
                NORTH_MIDLAT,
                SOUTH_MIDLAT,
                TROPICS,
                GLOBAL,
            ]
        }
    }

    rr = RegionRequest(request_dict)
    result = rr.submit()
    assert(result.success)

def test_request_get_specific_regions_by_name():
    request_dict = {
        'db_request_name': 'region',
        'method': db_utils.HTTP_GET,
        'params': {'filter_type': 'by_name'},
        'body': {
            'regions': [
                GLOBAL.get('name'),
                EQUATORIAL.get('name'),
                NORTH_MIDLAT.get('name'),
                SOUTH_MIDLAT.get('name'),
            ]
        }
    }

    rr = RegionRequest(request_dict)
    result = rr.submit()
    assert(result.success)

def test_request_get_specific_regions_by_region_data():
    request_dict = {
        'db_request_name': 'region',
        'method': db_utils.HTTP_GET,
        'params': {'filter_type': 'by_data', 'filters': {'east_lon': 0.0},},
    }

    rr = RegionRequest(request_dict)
    result = rr.submit()
    assert(result.success)

def test_request_all_regions():
    request_dict = {
        'db_request_name': 'region',
        'method': db_utils.HTTP_GET,
        'params': {'filter_type': 'none'},
        'body': {
            'regions': [
                GLOBAL,
                EQUATORIAL,
                NORTH_MIDLAT,
                SOUTH_MIDLAT,
            ]
        }
    }

    rr = RegionRequest(request_dict)
    result = rr.submit()
    assert(result.success)

    


