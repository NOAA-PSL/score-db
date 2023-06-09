"""
Copyright 2022 NOAA
All rights reserved.

Unit tests for io_utils

"""
import os
import pathlib
import pytest
import json
import yaml


from harvest_metrics import HarvestMetricsRequest
import score_table_models as scr_models
from score_table_models import Experiment as experiments_table
from score_table_models import ExperimentMetric as exp_metrics_table
import experiments as expts
import expt_metrics
from experiments import ExperimentData, Experiment, ExperimentRequest
from expt_metrics import ExptMetricInputData, ExptMetricRequest

from score_db_base import handle_request

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
            'expt_name': 'UFSRNR_GSI_SOCA_3DVAR_COUPLED_AZURE_HC44RS_122015',
            'expt_wallclock_start': '2022-08-03 02:40:34', 
            'datetime_str': '%Y-%m-%d %H:%M:%S',
        },
        'hv_translator': 'inc_logs',
        'harvest_config': {
            'harvester_name': 'inc_logs',
            'filename': FILE_PATH_ATM_INC_LOGS,
            'statistic': ['mean', 'RMS'],
            'variable': ['o3mr_inc', 'sphum_inc', 'T_inc', 'u_inc', 'v_inc',
                                  'delp_inc', 'delz_inc']
        }
    }

    hmr = HarvestMetricsRequest(db_harvester_dict)
    result = hmr.submit()
    print(f'Harvest atm inc log test results: {result}')