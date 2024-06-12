"""
Copyright 2023 NOAA
All rights reserved.

Collection of methods to translate results from harvesters
into input data relevant for storage in the columns defined in
the db table models.
"""

from collections import namedtuple

#data structure for what is stored in the database, corresponds to the db columns
#corresponds to singular input metric values 
MetricTableData = namedtuple(
    'MetricTableData',
    [
        'name',
        'region_name',
        'elevation',
        'elevation_unit',
        'value',
        'cycletime',
        'forecast_hour',
        'ensemble_member'
    ],
)

#corresponds to array structured metric values 
ArrayMetricTableData = namedtuple(
    'ArrayMetricTableData',
    [
        'name',
        'region_name',
        'value',
        'assimilated',
        'time_valid',
        'forecast_hour',
        'ensemble_member',
        'sat_meta_name',
        'sat_id',
        'sat_name',
        'sat_short_name',
    ],
) 

def inc_logs_translator(harvested_data):
    """ Expected output from inc_logs harvester 
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
    result = MetricTableData(
        harvested_data.statistic + "_" + harvested_data.variable,
        'global',
        None,
        'N/A',
        harvested_data.value,
        harvested_data.cycletime,
        None,
        None)
    return result

def daily_bfg_translator(harvested_data):
    """ Expected output from daily bfg harvester
    daily_bfg_harvested_data = namedtuple(
        'HarvestedData', 
        [
            'filenames',
            'statistic',
            'variable',
            'value',
            'units',
            'mediantime',
            'longname'
        ]
    )
    """
    result = MetricTableData(
        harvested_data.statistic + "_" + harvested_data.variable,
        'global',
        None,
        'N/A',
        harvested_data.value,
        harvested_data.mediantime,
        None,
        None
    )        
    
    return result
   
def gsi_satellite_radiance_translator(harvested_data):
    """Expected output from gsi_satellite_radiance harvester
    gsi_satellite_radiance_harvested_data = namedtuple(
        'SatinfoStat', [
            'datetime',
            'ensemble_member',
            'iteration',
            'observation_type', # radiance observation type (e.g., hirs2_tirosn)
            'series_numbers', # series numbers of the channels in satinfo file
            'channels', # channel numbers for certain radiance observation type
            'statistic', # name of statistic
            'values_by_channel',
            'longnames'
        ]
    )
    """
    instrument = harvested_data.observation_type.split('_')[0]
    sat_short_name = harvested_data.observation_type.split('_')[1]
    result = ArrayMetricTableData(
        instrument + "_" + harvested_data.statistic +
        "_GSIstage_" + str(harvested_data.iteration),
        'global',
        harvested_data.values_by_channel,
        None,
        harvested_data.datetime,
        None,
        harvested_data.ensemble_member,
        None,
        None,
        None,
        sat_short_name,
    )
    
    return result
