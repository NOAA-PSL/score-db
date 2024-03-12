"""
Copyright NOAA 2024
All rights reserved.

Collection of methods to facilitate handling of requests for array based experiment metrics.
Will also interact with the experiments, regions, array metric types, and sat meta tables. 
"""

from collections import namedtuple
import copy
from dataclasses import dataclass, field
from datetime import datetime
import json
import math
import pprint
import traceback

import numpy as np
from psycopg2.extensions import register_adapter, AsIs
from sqlalchemy import Integer, String, Boolean, DateTime, Float
import psycopg2
import pandas as pd
from pandas import DataFrame
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.inspection import inspect
from sqlalchemy import and_, or_, not_
from sqlalchemy import asc, desc
from sqlalchemy.sql import func
from sqlalchemy.orm import joinedload


from db_action_response import DbActionResponse
import score_table_models as stm
from score_table_models import Experiment as exp
from score_table_models import ExperimentMetric as ex_mt
from score_table_models import MetricType as mts
from score_table_models import Region as rgs
from experiments import Experiment, ExperimentData
from experiments import ExperimentRequest
import regions as rg
import metric_types as mt
import array_metric_types as amt
import time_utils
import db_utils

psycopg2.extensions.register_adapter(np.int64, psycopg2._psycopg.AsIs)
psycopg2.extensions.register_adapter(np.float32, psycopg2._psycopg.AsIs)
