"""
Copyright 2024 NOAA
All rights reserved.

Unit tests for instrument_meta.py

"""

from score_db.instrument_meta import InstrumentMetaRequest

def test_instrument_meta_put_request():
    request_dict = {
        'db_request_name': 'instrument_meta',
        'method' : 'PUT',
        'body' : {
            'name': 'example_instrument',
            'num_channels': 34,
            'scan_angle': 'The example of scan angle'
        }
    }

    imr = InstrumentMetaRequest(request_dict)
    result = imr.submit()
    print(f'Instrument Meta PUT results: {result}')
    assert(result.success)

def test_instrument_meta_get_request():
    request_dict = {
        'db_request_name': 'instrument_meta',
        'method': 'GET',
        'params' : {
            'filters' : {
                'name' : {
                    'exact' : 'example_instrument'
                }
            }
        }
    }

    imr = InstrumentMetaRequest(request_dict)
    result = imr.submit()
    print(f'Instrument Meta GET results: {result}')
    assert(result.success)
    assert(result.details.get('record_count') > 0)
