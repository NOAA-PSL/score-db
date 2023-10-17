"""Copyright 2023 NOAA
All rights reserved.

Collection of methods to translate results from harvesters
into input data relevant for storage in the columns defined in
the db table models.
"""

from collections import namedtuple

"""MetricTableData defines the data structure for what is stored in the 
database, which corresponds to the db columns.
"""

MetricTableData = namedtuple('MetricData', ['name',
                                            'region_name',
                                            'elevation',
                                            'elevation_unit',
                                            'value',
                                            'cycletime',
                                            'forecast_hour', 
                                            'ensemble_member'])

def inc_logs_translator(harvested_data):
    """Expected output from inc_logs harvester:
    
    inc_logs_harvested_data = namedtuple('HarvestedData', ['logfile',
                                                           'cycletime',
                                                           'statistic',
                                                           'variable',
                                                           'value',
                                                           'units'])
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


def precip_translator(harvested_data):
    """Expected output from precip harvester:
        
    precip_harvested_data = namedtuple('HarvestedData', ['filenames',
                                                         'statistic',
                                                         'variable',
                                                         'value',
                                                         'units',
                                                         'mediantime',
                                                         'longname'])
    """
    
    result = MetricTableData(
                       harvested_data.statistic + "_" + harvested_data.variable,
                       'global',
                       None,
                       'N/A'
                       harvested_data.value,
                       harvested_data.mediantime,
                       None,
                       None)        
    return result