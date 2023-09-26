"""
Copyright 2023 NOAA
All rights reserved.

Unit tests for plot file counts

"""
import os
import pathlib
import pytest
import json
import yaml

import plot_file_counts

plot_control_dict = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                    'end': '2000-01-01 00:00:00',
                                    'start': '1999-01-01 00:00:00'},
                     'db_request_name': 'expt_file_counts',
                     'method': 'GET',
                     'experiments': [{'graph_color': 'black',
                                      'graph_label': 'Number of files',
                                      'name': 'replay_stream2',
                                      'wallclock_start': '2023-07-24 17:56:40'}],
                     'fig_base_fn': 'files',
                     'stat_groups': [{'cycles': [0, 21600, 43200, 64800],
                                      'metrics': ['count'],
                                      'stat_group_frmt_str':
                                      'file_{metric}'}],
                     'work_dir': '/Users/jknezha/Development/results'}

def test_plot_file_count():
    plot_request = plot_file_counts.PlotFileCountRequest(plot_control_dict)
    plot_request.submit()

    print('finished')