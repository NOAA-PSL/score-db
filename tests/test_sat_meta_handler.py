"""
Copyright 2024 NOAA
All rights reserved.

Unit tests for sat_meta.py

"""

from score_db.sat_meta import SatMetaRequest


def test_sat_meta_put_request():
    request_dict = {
        'db_request_name': 'sat_meta',
        'method' : 'PUT',
        'body' :{
            'name': 'example_sat_meta',
            'sat_id': 123456789,
            'sat_name': 'Example Sat Name',
            'short_name': 'esm_1',
        }
    }

    smr = SatMetaRequest(request_dict)
    result = smr.submit()
    print(f'Sat Meta PUT results: {result}')
    assert(result.success)

def test_sat_meta_get_request():
    request_dict = {
        'db_request_name': 'sat_meta',
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
    assert(result.details.get('record_count') > 0)

def test_sat_meta_commit():
    put_request_dict = {
        'db_request_name': 'sat_meta',
        'method' : 'PUT',
        'body' :{
            'name': 'example_sat_meta',
            'sat_id': 123456789,
            'sat_name': 'Example Sat Name',
            'short_name': 'esm_1',
        }
    }

    smr_put = SatMetaRequest(put_request_dict)
    result_put = smr_put.submit()
    print(f'Sat Meta PUT results: {result_put}')
    id = result_put.details.get('id')

    get_request_dict = {
        'db_request_name': 'sat_meta',
        'method': 'GET',
        'params' : {
            'filters': {
                'id':id
                }
            }
        }

    smr_get = SatMetaRequest(get_request_dict)
    result_get = smr_get.submit()
    print(f'Sat Meta GET results: {result_get}')
    assert(result_get.success)
    assert(result_get.details.get('record_count') > 0)
