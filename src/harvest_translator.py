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
        'cycletime'
    ],
)


inc_logs_harvested_data = namedtuple(
    'HarvestedData',
    [
        'logfile',
        'statistic',
        'variable',
        'value',
        'units'
    ]
)
def inc_logs_translator(harvested_data):
    result = MetricData(
        harvested_data.statistic + "_" + harvested_data.variable,
        'global',
        0,
        'N/A',
        harvested_data.value, 
        '0001-01-01 00:00:00'
    )

    return result