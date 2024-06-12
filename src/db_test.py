#!/usr/bin/env python

"""store programs and data (request dictionaries) to interact with the
reanalysis experiment metrics database
"""

import json

import numpy as np

import score_db_base

def get_request_dict():
    
    request_dict = {
        'db_request_name': 'expt_file_counts',
        'method': 'GET',
    #    'params': {'filters':
    #                  {'experiment':
    #                      {'experiment_name':
    #                          {'exact':
    #                             'gefsv13replay_0.25d_v0.1'}}}
        #}
    }

    return request_dict

def get_request_dict2(db_request_name):
    request_dict = {
        'db_request_name': db_request_name,
        'method': 'GET',
        'params':{'filters':
                      {'experiment':
                          {'experiment_name':
                              {'exact':
                                 'scout_runs_gsi3dvar_1979stream'}}}
        }
    }
    return request_dict

def put_array_metric_type(name, measurement_type,
                          coordinate_labels,
                          coordinate_values,
                          coordinate_units,
                          coordinate_lengths,
                          instrument=None, obs_platform=None,
                          long_name=None,
                          measurement_units=None, stat_type=None,
                          description=None):
    request_dict = {
        'db_request_name': 'array_metric_types',
        'method': 'PUT',
        'body': {'instrument_meta_name': instrument,
                 'obs_platform': obs_platform,
                 'name': name,
                 'long_name': long_name,
                 'measurement_type': measurement_type,
                 'measurement_units': measurement_units,
                 'stat_type': stat_type,
                 'array_coord_labels': coordinate_labels,
                 'array_coord_units': coordinate_units,
                 'array_index_values': coordinate_values,
                 'array_dimensions': coordinate_lengths,
                 'description': json.dumps({"description": description})
        }}
    return score_db_base.handle_request(request_dict)

def register_instrument_meta(instrument_name, num_channels, scan_angle=None):
    request_dict = {'db_request_name': 'instrument_meta', 'method': 'PUT',
        'body': {'name': instrument_name,
                 'num_channels': num_channels
        }
    }
    return score_db_base.handle_request(request_dict)

def register_sat_meta(sat_name):
    request_dict = {'db_request_name': 'sat_meta', 'method': 'PUT',
        'body': {'sat_name': sat_name,
                 'short_name': sat_name,
                 'description': json.dumps({"description": None})
        }
    }
    return score_db_base.handle_request(request_dict)

def put_these_data():
    my_instruments = {'hirs2': 19,
                      'msu': 4,
                      'ssu': 2}
    for instrument, num_channels in my_instruments.items():
        register_instrument_meta(instrument, num_channels)

def put_these_sats():
    my_sats = ['tirosn']
    for sat in my_sats:
        register_sat_meta(sat)

def put_these_data2():
    my_instruments = {'hirs2': np.arange(1,20),
                      'msu': np.arange(1,5),
                      'ssu': np.arange(1,3)}
    my_stats = ('use', 'bias_pre_corr', 'bias_post_corr', 'std')
    its = (1, 2)

    for instrument, channels in my_instruments.items():
        for stat in my_stats:
            for gsi_stage in its:
                name = instrument + "_" + stat + "_GSIstage_" + str(gsi_stage)
                put_array_metric_type(name, 'brightness temperature',
                          ['channel'], channels,
                          ['number'],
                          [channels.size],
                          instrument=instrument, obs_platform='satellite',
                          long_name=None,
                          measurement_units='K', stat_type=stat,
                          description=None)

def run(request='array_metric_types'):
    return score_db_base.handle_request(get_request_dict2(request))

def main():
    run()

if __name__=='__main__':
    main()
