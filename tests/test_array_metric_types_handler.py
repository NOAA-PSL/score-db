"""
Copyright 2024 NOAA
All rights reserved.

Unit tests for array_metric_types.py

"""
import json
import numpy as np 
from array_metric_types import ArrayMetricTypeRequest

def test_put_array_metric_type_with_sat():
    request_dict = {
        'name': 'expt_array_metrics',
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
            'sat_meta_name': 'example_sat_meta',
            'sat_id': 123456789,
            'sat_name': 'Example Sat Name',
            'sat_sensor':'examplesensor',
            'sat_channel':'1'
        }
    }

    amtr = ArrayMetricTypeRequest(request_dict)
    result = amtr.submit()
    print(f'Array Metric Type PUT result: {result}')
    assert(result.success)


#TODO: write the get test for sat 
#TODO: write put and get test for non sat obs platform