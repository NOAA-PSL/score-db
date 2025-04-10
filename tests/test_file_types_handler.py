"""
Copyright 2023 NOAA
All rights reserved.

Unit tests for file_types.py

"""
import os
import pathlib
import pytest
import json
from collections import namedtuple

from score_db.file_types import FileTypeRequest


def test_file_type_input_dict():
    request_dict = {
        'db_request_name': 'file_types',
        'method' : 'PUT',
        'body' :{
            'name': 'example_type',
            'file_template': '*.example',
            'file_format': 'text',
            'description': json.dumps({"name": "example"})
        }
    }

    ftr = FileTypeRequest(request_dict)
    result = ftr.submit()
    print(f'File type PUT results: {result}')
    assert(result.success)

def test_file_type_get_request():
    request_dict = {
        'db_request_name': 'file_types',
        'method': 'GET',
        'params' : {
            'filters': {
                'name' :{
                    'exact' : 'example_type'
                }
            }
        }
    }

    ftr = FileTypeRequest(request_dict)
    result = ftr.submit()
    print(f'File type GET results: {result}')
    assert(result.success)
    assert(result.details.get('record_count') > 0)

def test_file_types_commit():
    put_request_dict = {
        'db_request_name': 'file_types',
        'method' : 'PUT',
        'body' :{
            'name': 'example_type',
            'file_template': '*.example',
            'file_format': 'text',
            'description': json.dumps({"name": "example"})
        }
    }

    ftr_put = FileTypeRequest(put_request_dict)
    result_put = ftr_put.submit()
    print(f'File type PUT results: {result_put}')
    id = result_put.details.get('id')

    get_request_dict = {
        'db_request_name': 'file_types',
        'method': 'GET',
        'params' : {
            'filters': {
                'id':id
                }
            }
    }

    ftr_get = FileTypeRequest(get_request_dict)
    result_get = ftr_get.submit()
    print(f'File type GET results: {result_get}')
    assert(result_get.success)
    assert(result_get.details.get('record_count') > 0)
