"""
Copyright 2023 NOAA
All rights reserved.

Unit tests for expt_file_counts.py

"""
import os
import pathlib
import pytest
import json


from expt_file_counts import ExptFileCountRequest

def test_put_expt_file_counts_request_dict():
    request_dict = {
        'name': 'expt_file_counts',
        'method': 'PUT',
        'body': {
            'experiment_name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'wallclock_start': '2021-07-22 09:22:05',
            'file_type_name': 'example_type',
            'file_extension': '.example',
            'time_valid': '2023-02-05 06:00:00',
            'forecast_length' : 120,
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

def test_get_expt_file_counts_dict():
    request_dict = {
        'name' : 'expt_file_counts',
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
            }
        }
    }

    efcr = ExptFileCountRequest(request_dict)
    result = efcr.submit()
    print(f'Expt File Counts GET results: {result}')

