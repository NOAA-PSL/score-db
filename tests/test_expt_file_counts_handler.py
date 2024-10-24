"""
Copyright 2023 NOAA
All rights reserved.

Unit tests for expt_file_counts.py

"""
import os
import pathlib
import pytest
import json


from score_db.expt_file_counts import ExptFileCountRequest

def test_put_expt_file_counts_request_dict():
    request_dict = {
        'db_request_name': 'expt_file_counts',
        'method': 'PUT',
        'body': {
            'experiment_name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'wallclock_start': '2021-07-22 09:22:05',
            'file_type_name': 'example_type',
            'file_extension': '.example',
            'time_valid': '2023-02-05 06:00:00',
            'forecast_hour' : 120,
            'file_size_bytes': 120394945934, 
            'bucket_name' : 'noaa-example-score-db-bucket',
            'platform': 'aws_s3',
            'key': 'reanalysis',
            'count': 1230,
            'folder_path': 'noaa-example-score-db-bucket/reanalysis/2023/02/23/2023022306',
            'cycle': '2023-02-03 06:00:00'
        }
    }

    efcr = ExptFileCountRequest(request_dict)
    result = efcr.submit()
    print(f'Expt File Counts PUT results: {result}')
    assert(result.success)

def test_get_expt_file_counts_dict():
    request_dict = {
        'db_request_name' : 'expt_file_counts',
        'method': 'GET',
        'params' : {
            'filters': {
                'experiment': {
                    'experiment_name': {
                        'exact': 'C96L64.UFSRNR.GSI_3DVAR.012016'
                    }
                },
                'file_types': {
                    'file_type_name': {
                        'exact': 'example_type',
                    },
                },
                'storage_locations': {
                    'storage_loc_name' :{
                        'exact': 's3_example_bucket',
                    },
                },
                'forecast_hour': 120
            }
        }
    }

    efcr = ExptFileCountRequest(request_dict)
    result = efcr.submit()
    print(f'Expt File Counts GET results: {result}')
    assert(result.success)
    assert(result.details.get('record_count') > 0)

def test_get_expt_file_counts_dict_only_count_filter():
    request_dict = {
        'db_request_name' : 'expt_file_counts',
        'method': 'GET',
        'params' : {
            'filters': {
                'count': 1230,
                'folder_path': {
                    'exact': 'noaa-example-score-db-bucket/reanalysis/2023/02/23/2023022306'
                }
            },
            
        }
    }

    efcr = ExptFileCountRequest(request_dict)
    result = efcr.submit()
    print(f'Expt File Counts GET results: {result}')
    assert(result.success)
    assert(result.details.get('record_count') > 0)

