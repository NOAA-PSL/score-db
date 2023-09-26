"""
Copyright 2023 NOAA
All rights reserved.

Unit tests for plot increments

"""
import os
import pathlib
import pytest
import json
import yaml

import plot_increments

plot_control_dict = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                    'end': '2000-01-01 00:00:00',
                                    'start': '1999-01-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{'graph_color': 'black',
                                      'graph_label': 'increments',
                                      'name': 'replay_stream2',
                                      'wallclock_start': '2023-07-24 17:56:40'}],
                     'fig_base_fn': 'increment',
                     'stat_groups': [{'cycles': [0, 21600, 43200, 64800],
                                      'stats': ['mean', 'RMS'],
                                      'metrics': ['pt_inc', 's_inc', 'u_inc',
                                                  'v_inc', 'SSH', 'Salinity',
                                                  'Temperature',
                                                  'Speed of Currents', 'o3mr_inc',
                                                  'sphum_inc', 'T_inc', 'delp_inc',
                                                  'delz_inc'],
                                      'stat_group_frmt_str':
                                      'metric_type_{stat}_{metric}'}],
                     'work_dir': '/Users/jknezha/Development/results'}


def test_plot_increment():
    plot_request = plot_increments.PlotIncrementRequest(plot_control_dict)
    plot_request.submit()

    print('finished')


