"""
Copyright 2024 NOAA
All rights reserved.

Unit tests for array_metric_types.py

"""
import json
import numpy as np 
from array_metric_types import ArrayMetricTypeRequest

def test_put_array_metric_type_with_instrument():
    request_dict = {
        'name': 'array_metric_types',
        'method': 'PUT',
        'body': {
            'name': 'vertical_example_metric',
            'longname': 'vertical long name example',
            'obs_platform': 'satellite',
            'measurement_type': 'example_measurement_type',
            'measurement_units': 'example_measurement_units',
            'stat_type': 'example_stat',
            'array_coord_labels': ['temperature', 'elevation'],
            'array_coord_units': ['K', 'feet'],
            'array_index_values': [[10, 20, 30],[1000, 5000, 10000]],
            'array_dimensions': [3, 3],
            'description': json.dumps("example array metric type for testing purposes"),
            'instrument_meta_name': 'example_instrument',
        }
    }

    amtr = ArrayMetricTypeRequest(request_dict)
    result = amtr.submit()
    print(f'Array Metric Type PUT result: {result}')
    assert(result.success)

def test_get_array_metric_type_with_instrument():
    request_dict = {
        'name':'array_metric_types',
        'method':'GET',
        'params':{
            'filters':{
                'name':{
                    'exact':'vertical_example_metric'
                },
                'instrument_meta_name':{
                    'exact': 'example_instrument'
                },
                'stat_type':{
                    'exact':'example_stat'
                }
            },
            'limit':1
        }
    }

    amtr = ArrayMetricTypeRequest(request_dict)
    result = amtr.submit()
    print(f'Array Metric Type GET result: {result}')
    assert(result.success)
    assert(result.details.get('record_count') > 0)

def test_put_array_metric_type_no_instrument():
    request_dict = {
        'name': 'array_metric_types',
        'method': 'PUT',
        'body': {
            'name': 'vertical_example_metric2',
            'longname': 'vertical long name example #2',
            'obs_platform': 'insitu',
            'measurement_type': 'example_measurement_type2',
            'measurement_units': 'example_measurement_units2',
            'stat_type': 'example_stat2',
            'array_coord_labels': ['temperature', 'depth'],
            'array_coord_units': ['K', 'm'],
            'array_index_values': [[10, 20, 30],[1000, 5000, 10000]],
            'array_dimensions': [3, 3],
            'description': json.dumps("example array metric type for testing purposes with no sat")
        }
    }

    amtr = ArrayMetricTypeRequest(request_dict)
    result = amtr.submit()
    print(f'Array Metric Type PUT result: {result}')
    assert(result.success)

def test_get_array_metric_type_no_instrument():
    request_dict = {
        'name':'array_metric_types',
        'method':'GET',
        'params':{
            'filters':{
                'name':{
                    'exact':'vertical_example_metric2'
                },
                'stat_type':{
                    'exact':'example_stat2'
                }
            },
            'limit':1
        }
    }

    amtr = ArrayMetricTypeRequest(request_dict)
    result = amtr.submit()
    print(f'Array Metric Type GET result: {result}')
    assert(result.success)
    assert(result.details.get('record_count') > 0)