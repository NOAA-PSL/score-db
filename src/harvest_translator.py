"""
Copyright 2023 NOAA
All rights reserved.

Collection of methods to translate results from harvesters
into input data relevant for storage in the columns defined in
the db table models. 

"""

from collections import namedtuple

MetricData = namedtuple(
    'MetricData',
    [
        'name',
        'region_name',
        'elevation',
        'elevation_unit',
        'value',
        'time_valid'
    ],
)


inc_log_harvested_data = namedtuple(
    'HarvestedData',
    [
        'logfile',
        'statistic',
        'variable',
        'value',
        'units'
    ]
)
def inc_log_translator(harvested_data):
    result = MetricData(
        harvested_data.statistic + "_" + harvested_data.variable,
        'global',
        0,
        'N/A',
        harvested_data.value, 
        'Jan 01 0001 00:00:00'
    )

    return result