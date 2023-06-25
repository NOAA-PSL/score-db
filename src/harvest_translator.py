"""
Copyright 2023 NOAA
All rights reserved.

Collection of methods to translate results from harvesters
into input data relevant for storage in the columns defined in
the db table models. 

"""

from collections import namedtuple

#data structure for what is stored in the database, corresponds to the db columns
MetricTableData = namedtuple(
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

"""
Expected output from inc_logs harvester 
inc_logs_harvested_data = namedtuple(
    'HarvestedData',
    [
        'logfile',
        'cycletime',
        'statistic',
        'variable',
        'value',
        'units'
    ]
)
"""
def inc_logs_translator(harvested_data):
    result = MetricTableData(
        harvested_data.statistic + "_" + harvested_data.variable,
        'global',
        None,
        'N/A',
        harvested_data.value, 
        harvested_data.cycletime
    )

    return result