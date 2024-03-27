"""
Copyright 2024 NOAA
All rights reserved.

Unit tests for sat_meta.py

"""

from sat_meta import SatMetaRequest


def test_sat_meta_input_dict():
    request_dict = {
        'name': 'sat_meta',
        'method' : 'PUT',
        'body' :{
            'name': 'example_sat_meta',
            'sat_id': 123456789,
            'sat_name': 'Example Sat Name',
            'sensor': 'examplesensor',
            'channel': '1',
            'scan_angle':'90 degreees sectors fore- and aft-'
        }
    }

    smr = SatMetaRequest(request_dict)
    result = smr.submit()
    print(f'Sat Meta PUT results: {result}')
    assert(result.success)

def test_sat_meta_get_request():
    request_dict = {
        'name': 'sat_meta',
        'method': 'GET',
        'params' : {
            'filters': {
                'name' :{
                    'exact' : 'example_sat_meta'
                }
            }
        }
    }

    smr = SatMetaRequest(request_dict)
    result = smr.submit()
    print(f'Sat Meta GET results: {result}')
    assert(result.success)
