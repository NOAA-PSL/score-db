"""
Copyright 2022 NOAA
All rights reserved.

Unit tests for expt_metrics.py

"""

from score_db.expt_metrics import ExptMetricInputData, ExptMetricRequest

def test_put_exp_metrics_request_dict():

    request_dict = {
        'db_request_name': 'expt_metrics',
        'method': 'PUT',
        'body': {
            'expt_name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'expt_wallclock_start': '2021-07-22 09:22:05',
            'metrics': [
                ExptMetricInputData('innov_stats_temperature_rmsd', 'global', '0', 'kpa', 2.6, '2015-12-02 06:00:00', None, None),
                ExptMetricInputData('innov_stats_uvwind_rmsd', 'tropics', '50', 'kpa', 2.8, '2015-12-02 06:00:00', 24, 256)
            ],
            'datestr_format': '%Y-%m-%d %H:%M:%S'
        }
    }

    emr = ExptMetricRequest(request_dict)
    result = emr.submit()
    print(f'Experiment metrics PUT result: {result}')
    assert(result.success)

def test_send_get_request():

    request_dict = {
        'db_request_name': 'expt_metrics',
        'method': 'GET',
        'params': {
            'datestr_format': '%Y-%m-%d %H:%M:%S',
            'filters': {
                'experiment': {
                    'name': {
                        'exact': 'C96L64.UFSRNR.GSI_3DVAR.012016',
                    },
                    'wallclock_start': {
                        'from': '2021-07-22 02:22:05',
                        'to': '2021-07-22 10:22:05'
                    }
                },
                'metric_types': {
                    'name': {
                        'exact': ['innov_stats_temperature_rmsd']
                    },
                    'stat_type': {
                        'exact': ['rmsd']
                    }
                },
                'regions': {
                    'name': {
                        'exact': ['global']
                    },
                },

                'time_valid': {
                    'from': '2015-01-01 00:00:00',
                    'to': '2016-01-03 00:00:00',
                },
            },
            'ordering': [
                # {'name': 'id', 'order_by': 'asc'}
                {'name': 'time_valid', 'order_by': 'asc'}
            ]
        }
    }

    emr = ExptMetricRequest(request_dict)
    result = emr.submit()
    assert(result.success)
    assert(result.details.get('record_count') > 0)
