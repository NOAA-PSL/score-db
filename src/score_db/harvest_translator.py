"""
Copyright 2023 NOAA
All rights reserved.

Collection of methods to translate results from harvesters
into input data relevant for storage in the columns defined in
the db table models.
"""

import warnings
from collections import namedtuple

#data structure for what is stored in the database, corresponds to the db columns
#corresponds to singular input metric values 
MetricTableData = namedtuple(
    'MetricTableData',
    [
        'name',
        'region_name',
        'region_min_lat',
        'region_max_lat',
        'region_east_lon',
        'region_west_lon',
        'elevation',
        'elevation_unit',
        'value',
        'cycletime',
        'forecast_hour',
        'ensemble_member',
        'level',
        'sat_meta_name',
        'sat_id',
        'sat_name',
        'sat_short_name',
    ],
)

#corresponds to array structured metric values 
ArrayMetricTableData = namedtuple(
    'ArrayMetricTableData',
    [
        'name',
        'region_name',
        'region_min_lat',
        'region_max_lat',
        'region_east_lon',
        'region_west_lon',
        'value',
        'assimilated',
        'time_valid',
        'forecast_hour',
        'ensemble_member',
        'level',
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
        None,
        None,
        None,
        None,
        'N/A',
        harvested_data.value,
        harvested_data.cycletime,
        None,
        None,
        None,
        None, 
        None,
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
        None,
        None,
        None,
        None,
        'N/A',
        harvested_data.value,
        harvested_data.mediantime,
        None,
        None,
        None,
        None, 
        None,
        None,
        None
    )        
    
    return result
   
def gsi_satellite_radiance_channel_translator(harvested_data):
    """Expected output from gsi_satellite_radiance_channel harvester
    gsi_satellite_radiance_channel_harvested_data = namedtuple(
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

    if harvested_data.ensemble_member == 'control':
        ensemble_member = None
    else:
        try:
            ensemble_member = int(harvested_data.ensemble_member)
        except ValueError:
            warnings.warn('could not convert harvested_data.ensemble_member '
                          f'{harvested_data.ensemble_member} to int, storing '
                          f'as NoneType')
            ensemble_member = None

    result = ArrayMetricTableData(
        instrument + "_" + harvested_data.statistic +
        "_GSIstage_" + str(harvested_data.iteration),
        'global',
        None,
        None,
        None,
        None,
        harvested_data.values_by_channel,
        None,
        harvested_data.datetime,
        None,
        ensemble_member,
        None,
        None,
        None,
        None,
        sat_short_name,
    )
    
    return result
    
def soca_diags_translator(harvested_data):
    """Expected output from soca_diags harvester
    HarvestedData = namedtuple('HarvestedData',
        ['filenames',
         'sensor',
         'satellite',
         'level',
         'variables',
         'group',
         'longname',
         'units',
         'statistics',
         'value',
         'filetime',
         'file_region']
    )
    """
    
    if harvested_data.sensor is None:
        instrument_type = 'insitu'
    else:
        instrument_type = harvested_data.sensor
    
    result = MetricTableData(
        harvested_data.statistics + "_" + harvested_data.variables "_" +
        instrument_type + "_" + harvested_data.group, # name
        harvested_data.file_region, # region_name
        None, # region_min_lat
        None, # region_max_lat,
        None, # region_east_lon
        None, # region_west_lon
        None, # elevation
        'N/A', # elevation_unit
        harvested_data.value, # value
        harvested_data.filetime, # cycletime
        None, # ensemble_member
        harvested_data.level, # level
        None, # sat_meta_name
        None, # sat_id
        None, # sat_name
        harvested_data.satellite, # sat_short_name
    )
    
    return result