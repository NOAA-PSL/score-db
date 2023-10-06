"""
Copyright 2023 NOAA
All rights reserved.

Unit tests for storage_locations.py

"""
import pytest 
from storage_locations import StorageLocationRequest


def test_storage_location_input_dict():
    request_dict = {
        'name': 'storage_locations',
        'method': 'PUT',
        'body': {
            'name': 's3_example_bucket',
            'platform': 'aws_s3', 
            'bucket_name': 'noaa-example-score-db-bucket',
            'key': 'reanalysis',
            'platform_region': 'n/a'
        }
    }

    slr = StorageLocationRequest(request_dict)
    result = slr.submit()
    print(f'Storage locations PUT result: {result}')
    assert(result.success)

def test_storage_location_get_request():
    request_dict = {
        'name': 'storage_locations',
        'method': 'GET',
        'params': {
            'datestr_format': '%Y-%m-%d %H:%M:%S',
            'filters': {
                'name': {
                    'exact': 's3_example_bucket'
                },
            }
        }
    }

    slr = StorageLocationRequest(request_dict)
    result = slr.submit()
    print(f'Storage location GET result: {result}')
    assert(result.success)