"""
Copyright 2023 NOAA
All rights reserved.

Collection of methods to coordinate harvesting of metrics via the score-hv
harvester options.  The harvested metrics will be inserted
into the centralized database for easy access at any later time.

"""
from collections import namedtuple
import copy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import pprint
import traceback
import hv_translator_registry as hvtr 
from db_action_response import DbActionResponse

import time_utils
from time_utils import DateRange
from score_hv.harvester_base import harvest
from expt_metrics import ExptMetricInputData, ExptMetricRequest

@dataclass
class HarvestMetricsRequest(object):
    request_dict: dict
    body: dict = field(default_factory=dict, init=False)
    harvest_config: dict = field(default_factory=dict, init=False)
    expt_name: str = field(default_factory=str, init=False)
    expt_wallclock_start: datetime = field(default_factory=datetime, init=False) 
    datetime_str: str = field(default_factory=str, init=False)
    hv_translator: str = field(default_factory=str, init=False)

    def __post_init__(self):
        self.body = self.request_dict.get('body')
        self.hv_config = self.request_dict.get('harvest_config')
        self.hv_translator = self.request_dict.get('hv_translator')

        self.expt_name = self.body.get('expt_name')
        self.expt_wallclock_start = self.body.get('expt_wallclock_start')
        self.datetime_str = self.body.get('datetime_str')

    def failed_request(self, error_msg):
        return DbActionResponse(
            request=self.request_dict,
            success=False,
            message='Failed harvest metric request.',
            details=None,
            errors=error_msg
        )

    def submit(self):
        # get harvested data
        print(f'harvest config: {self.hv_config}')
        harvested_data = harvest(self.hv_config)

        expt_metrics = []
        print(f'harvested_data: type: {type(harvested_data)}')
        for row in harvested_data:
            data = ""
            #Call appropriate translator if one is provided
            if self.hv_translator != "":
                try:
                    translator = hvtr.translator_registry.get(self.hv_translator)
                    data = translator.translate(row)
                except Exception as err: 
                    error_message = f"An error occurred when translating the data with translator {self.hv_translator}. Error: {err}"
                    return self.failed_request(error_message)

            item = ExptMetricInputData(
                data.name,
                data.region_name,
                data.elevation,
                data.elevation_units,
                data.value,
                data.cycletime
            )

            expt_metrics.append(item)

        request_dict = {
            'name': 'expt_metrics',
            'method': 'PUT',
            'body': {
                'expt_name': self.expt_name,
                'expt_wallclock_start': self.expt_wallclock_start,
                'metrics': expt_metrics,
                'datestr_format': self.datetime_str
            }
        }

        emr = ExptMetricRequest(request_dict)
        result = emr.submit()
        return result
