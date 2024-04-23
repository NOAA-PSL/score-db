"""
Copyright 2022 NOAA
All rights reserved. 

Unit tests for expt_array_metrics.py
"""

from expt_array_metrics import ExptArrayMetricInputData, ExptArrayMetricRequest

#TODO: NEED TO TEST IF WE CAN GIVE JUST PART OF THE SAT META INFO TO GET THE ID

#TODO: the expt array input data has sat stuff now! and no bias correction 

def test_put_exp_array_metrics_request():
    request_dict = {
        'name': 'expt_array_metrics',
        'method': 'PUT',
        'body': {
            'expt_name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'expt_wallclock_start': '2021-07-22 09:22:05',
            'array_metrics': [
                ExptArrayMetricInputData('vertical_example_metric','global',[[1, 2, 3],[4, 5, 6],[7, 8, 9]], [[0, 1, 0],[1, 0, 1],[0, 0, 1]], True, '2015-12-02 06:00:00', None, None),
                ExptArrayMetricInputData('vertical_example_metric2','global',[[111, 222, 333],[444, 555, 666],[777, 888, 999]], [[1, 1, 0],[1, 0, 1],[1, 0, 0]], True, '2015-12-02 18:00:00', 24, 12)
            ],
            'datestr_format': '%Y-%m-%d %H:%M:%S'
        }
    }

    eamr = ExptArrayMetricRequest(request_dict)
    result = eamr.submit()
    print(f'Experiment Array Metrics PUT result: {result}')
    assert(result.success)

def test_get_expt_array_metrics_request():

    request_dict = {
        'name': 'expt_array_metrics',
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
                        'exact': ['vertical_example_metric']
                    },
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
                {'name': 'time_valid', 'order_by': 'asc'}
            ]
        }
    }

    eamr = ExptArrayMetricRequest(request_dict)
    result = eamr.submit()
    assert(result.success)
    assert(result.details.get('record_count') > 0)