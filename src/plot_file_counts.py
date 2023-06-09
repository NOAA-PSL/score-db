"""
Copyright 2023 NOAA
All rights reserved.

Collection of methods to facilitate handling of score db requests

import copy

from datetime import datetime
import json
import matplotlib.pylab as pl
import numpy as np
import os
import pathlib

import pprint
import traceback

import time_utils
from time_utils import DateRange
from score_hv.harvester_base import harvest
"""
from dataclasses import dataclass, field
from collections import namedtuple
from datetime import datetime

import pandas as pd
from pandas import DataFrame
from matplotlib import pyplot as plt


from expt_file_counts import ExptFileCountRequest
from file_counts_plot_attrs import plot_attrs
from plot_innov_stats import PlotInnovStatsRequest

RequestData = namedtuple('RequestData', ['datetime_str', 'experiment',
                                         'metric_format_str', 'metric',
                                         'time_valid'],)
plot_control_dict = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                    'end': '2019-03-22 00:00:00',
                                    'start': '2019-03-21 00:00:00'},
                     'db_request_name': 'expt_file_counts',
                     'method': 'GET',
                     'experiments': [{'graph_color': 'black',
                                      'graph_label': 'Number of files',
                                      'name': 'replay spinup stream 4',
                                      'wallclock_start': '2023-01-01 00:00:00'}],
                     'fig_base_fn': 'file_counts',
                     'stat_groups': [{'cycles': [0, 21600, 43200, 64800],
                                      'metrics': ['count'],
                                      'stat_group_frmt_str':
                                      'file_{metric}'}],
                     'work_dir': '/contrib/Adam.Schneider/replay/results'}
'''
@dataclass
class StatGroupData:
    stat_group_dict: dict
    cycles: list = field(default_factory=list, init=False)
    stat_group_frmt_str: str = field(default_factory=str, init=False)
    metrics: list[str] = field(init=False)
    stats: list[str] = field(init=False)
    regions: list[str] = field(init=False)
    elevation_unit: str = field(init=False)

    def __post_init__(self):
        self.cycles = self.stat_group_dict.get('cycles')
        self.stat_group_frmt_str = self.stat_group_dict.get('stat_group_frmt_str')
        self.metrics = self.stat_group_dict.get('metrics')
        self.stats = self.stat_group_dict.get('stats')
        self.regions = self.stat_group_dict.get('regions')
        self.elevation_unit = self.stat_group_dict.get('elevation_unit')

'''
def get_experiment_file_counts(request_data):
    
    expt_metric_name = request_data.metric_format_str.replace(
                                                        '{metric}', 
                                                        request_data.metric)

    time_valid_from = datetime.strftime(request_data.time_valid.start, 
                                        request_data.datetime_str)

    time_valid_to = datetime.strftime(request_data.time_valid.end, 
                                      request_data.datetime_str)

    request_dict = {
     'name': 'expt_file_counts',
     'method': 'GET',
     'params': {'datestr_format': request_data.datetime_str,
                'filters': {#'experiment': request_data.experiment,    
                            #'metric_types': {'name': {'exact': 
                            #                             [expt_metric_name]}},
                            'time_valid': {'from': time_valid_from,
                                           'to': time_valid_to,}},
                'ordering': [{'name': 'time_valid', 'order_by': 'asc'},
                             {'name': 'count', 'order_by': 'desc'}]}}

    print(f'request_dict: {request_dict}')

    efcr = ExptFileCountRequest(request_dict)
    result = efcr.submit()

    return result.details['records']

def build_base_figure():
    fig, ax = plt.subplots()
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tick_params(axis='x', which='both', bottom=False, top=False,
                    labelbottom=True)
    
    return(fig, ax)


def format_figure(ax, pa):
    ax.set_xlim([pa.axes_attrs.xmin, pa.axes_attrs.xmax])
    ax.set_ylim([pa.axes_attrs.ymin, pa.axes_attrs.ymax])
    
    plt.xticks(np.arange(pa.axes_attrs.xmin, (pa.axes_attrs.xmax + 1.e-6),
                         pa.axes_attrs.xint))
    
    plt.xlabel(xlabel=pa.xlabel.label,
               horizontalalignment=pa.xlabel.horizontalalignment)
    
    plt.ylabel(ylabel=pa.ylabel.label,
               horizontalalignment=pa.ylabel.horizontalalignment)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.legend(loc=pa.legend.loc,
               fancybox=pa.legend.fancybox,
               edgecolor=pa.legend.edgecolor,
               framealpha=pa.legend.framealpha,
               shadow=pa.legend.shadow,
               facecolor=pa.legend.facecolor)

def build_fig_dest(work_dir, fig_base_fn, metric, date_range):
    
    start = datetime.strftime(date_range.start, '%Y%m%dT%HZ')
    end = datetime.strftime(date_range.end, '%Y%m%dT%HZ')
    dest_fn = fig_base_fn
    dest_fn += f'__{metric}_{start}_to_{end}.png'
    
    dest_full_path = os.path.join(work_dir, dest_fn)
    
    parent_dir = pathlib.Path(dest_full_path).parent
    pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
    
    return dest_full_path

def save_figure(dest_full_path):
    print(f'saving figure to {dest_full_path}')
    plt.savefig(dest_full_path)

def plot_file_counts(experiments, metric, metrics_df, work_dir, fig_base_fn,
                     date_range):

    if not isinstance(metrics_df, DataFrame):
        msg = 'Input data to plot_innov_stats must be type pandas.DataFrame '\
            f'was actually type: {type(metrics_df)}'
        raise TypeError(msg)
    
    plt_attr_key = f'{metric}'
    pa = plot_attrs[plt_attr_key]
    
    ave_df = metrics_df.groupby(['expt_name', 'count'], 
                                as_index=False)['value'].mean()
    
    expt_names = ave_df.drop_duplicates(
                    ['expt_name'], keep='last')['expt_name'].values.tolist()

    (fig, ax) = build_base_figure()

    for expt in experiments:
        expt_name = expt.get('expt_name')
        stat_vals = ave_df.loc[(ave_df['expt_name'] == expt_name), 'value']

        plt.plot(stat_vals, color=expt.get('graph_color'),
                 label=expt.get('graph_label'))
    
    format_figure(ax, pa)
    fig_fn = build_fig_dest(work_dir, fig_base_fn, metric, region, date_range)

    save_figure(fig_fn)

'''''
@dataclass
class ExperimentData(object):
    name: str
    wallclock_start: str
    graph_color: str
    graph_label: str
    
    def get_dict(self):
        return {
            'name': {
                'exact': self.name
            },
            'wallclock_start': {
                'from': self.wallclock_start,
                'to': self.wallclock_start
            },
            'expt_name': self.name,
            'expt_start': self.wallclock_start,
            'graph_label': self.graph_label,
            'graph_color': self.graph_color
        }

'''
@dataclass
class PlotFileCountRequest(PlotInnovStatsRequest):
    def submit(self):
        master_list = []
        n_hours = 6
        n_days = 0

        finished = False
        loop_count = 0
        
        for stat_group in self.stat_groups:
            metrics_data = []
            # gather experiment metrics data for experiment and date range
            for metric in stat_group.metrics:
                m_df = DataFrame()
                for experiment in self.experiments:
                    request_data = RequestData(
                        self.datetime_str,
                        experiment,
                        stat_group.stat_group_frmt_str,
                        metric,
                        self.date_range)
                        
                    e_df = get_experiment_file_counts(request_data)
                    e_df = e_df.sort_values(['expt_name', 'count'])
                    m_df = pd.concat([m_df, e_df], axis=0)

                plot_file_counts(
                    self.experiments,
                    metric,
                    m_df,
                    self.work_dir,
                    self.fig_base_fn,
                    self.date_range)

if __name__=='__main__':
    plot_request = PlotFileCountRequest(plot_control_dict)
    plot_request.submit()
