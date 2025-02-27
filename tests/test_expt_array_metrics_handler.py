"""
Copyright 2022 NOAA
All rights reserved. 

Unit tests for expt_array_metrics.py
"""

from score_db.expt_array_metrics import ExptArrayMetricInputData, ExptArrayMetricRequest
from time import time

def test_put_exp_array_metrics_request():
    request_dict = {
        'db_request_name': 'expt_array_metrics',
        'method': 'PUT',
        'body': {
            'expt_name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'expt_wallclock_start': '2021-07-22 09:22:05',
            'array_metrics': [
                ExptArrayMetricInputData('vertical_example_metric','global',[[1, 2, 3],[4, 5, 6],[7, 8, 9]], True, '2015-12-02 06:00:00', None, None, None, None, None, None),
                ExptArrayMetricInputData('vertical_example_metric2','global',[[111, 222, 333],[444, 555, 666],[777, 888, 999]], True, '2015-12-02 18:00:00', 24, 12, None, None, None, None)
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
        'db_request_name': 'expt_array_metrics',
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
                'array_metric_types': {
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

def test_put_exp_array_metrics_request_with_sat():
    request_dict = {
        'db_request_name': 'expt_array_metrics',
        'method': 'PUT',
        'body': {
            'expt_name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'expt_wallclock_start': '2021-07-22 09:22:05',
            'array_metrics': [
                ExptArrayMetricInputData('vertical_example_metric','global',[[1, 2, 3],[4, 5, 6],[7, 8, 9]], True, '2015-12-02 06:00:00', None, None, 'example_sat_meta', None, None, None),
                ExptArrayMetricInputData('vertical_example_metric2','global',[[111, 222, 333],[444, 555, 666],[777, 888, 999]], True, '2015-12-02 18:00:00', 24, 12, 'example_sat_meta', 123456789, 'Example Sat Name', 'esm_1')
            ],
            'datestr_format': '%Y-%m-%d %H:%M:%S'
        }
    }

    eamr = ExptArrayMetricRequest(request_dict)
    result = eamr.submit()
    print(f'Experiment Array Metrics PUT result: {result}')
    assert(result.success)

def test_get_expt_array_metrics_request_with_sat():

    request_dict = {
        'db_request_name': 'expt_array_metrics',
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
                'array_metric_types': {
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
                'sat_meta': {
                    'name': {
                        'exact' : 'example_sat_meta'
                    }
                }
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


def test_get_expt_array_metrics_request_timing():

    request_dict = {
        'db_request_name': 'expt_array_metrics',
        'method': 'GET',
        'params': {
            'datestr_format': '%Y-%m-%d %H:%M:%S',
            'filters': {
                'experiment': {
                    'experiment_name': {
                        'exact': ['scout_run_v1', 'NASA_GEOSIT_GSISTATS']
                    },
                    # 'wallclock_start': {
                    #     'from': '2021-07-22 02:22:05',
                    #     'to': '2021-07-22 10:22:05'
                    # }
                },
                'array_metric_types': {
                    'name': {
                        'exact': ['amsua_std_GSIstage_1']
                    },
                    #'id': 361 
                },
                'regions': {
                    'rgs_name': {
                        'exact': ['global']
                    },
                },

                # 'time_valid': {
                #     'from': '2015-01-01 00:00:00',
                #     'to': '2016-01-03 00:00:00',
                # },
            },
            # 'ordering': [
            #     {'name': 'time_valid', 'order_by': 'asc'}
            # ]
        }
    }

    eamr = ExptArrayMetricRequest(request_dict)
    start = time()
    result = eamr.submit()
    end = time()
    elapsed_time_ms = (end - start) * 1000
    duration_string = f"Execution time: {elapsed_time_ms:.4f} ms"
    assert(result.success)
    assert(result.details.get('record_count') > 0)