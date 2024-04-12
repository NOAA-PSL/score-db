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

from file_types import FileTypeRequest


def test_file_type_input_dict():
    request_dict = {
        'name': 'file_types',
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
        'name': 'file_types',
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
