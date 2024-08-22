"""
Copyright 2022 NOAA
All rights reserved.

Unit tests for io_utils

"""
import os
import pathlib

from score_db.harvest_metrics import HarvestMetricsRequest

from score_db.score_db_base import handle_request

PYTEST_CALLING_DIR = pathlib.Path(__file__).parent.resolve()
DATA_DIR = 'experiment-data'
LOG_HARVESTER_ATM__VALID = 'calc_atm_inc.out'

TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, DATA_DIR)
FILE_PATH_ATM_INC_LOGS = os.path.join(TEST_DATA_PATH,
                                      LOG_HARVESTER_ATM__VALID)

def test_run_atm_inc_log_harvester():
    db_harvester_dict = {
        'db_request_name': 'harvest_metrics',
        'body': {
            'expt_name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'expt_wallclock_start': '2021-07-22 09:22:05', 
            'datetime_str': '%Y-%m-%d %H:%M:%S',
        },
        'hv_translator': 'inc_logs',
        'harvest_config': {
            'harvester_name': 'inc_logs',
            'filename': FILE_PATH_ATM_INC_LOGS,
            'statistic': ['mean'],
            'variable': ['o3mr_inc'],
            'cycletime': '1995-01-01 00:00:00'
        }
    }

    hmr = HarvestMetricsRequest(db_harvester_dict)
    result = hmr.submit()
    print(f'Harvest atm inc log test results: {result}')
    assert(result.success)
