"""
Copyright 2023 NOAA
All rights reserved.

Collection of methods to facilitate handling of score db requests

import copy

import json

import pprint
import traceback

import time_utils
from time_utils import DateRange
from score_hv.harvester_base import harvest
"""
import os
import pathlib
from dataclasses import dataclass, field
from collections import namedtuple
from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame
from matplotlib import pyplot as plt


from expt_metrics import ExptMetricRequest
from increments_plot_attrs import plot_attrs
from plot_innov_stats import PlotInnovStatsRequest

import ipdb

RequestData = namedtuple('RequestData', ['datetime_str', 'experiment',
                                         'metric_format_str', 'metric',
                                         'stat',
                                         'time_valid'],)
plot_control_dict = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                    'end': '2020-01-01 00:00:00',
                                    'start': '2019-01-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{'graph_color': 'black',
                                      'graph_label': 'increments',
                                      'name': 'replay_stream4',
                                      'wallclock_start': '2023-01-01 00:00:00'}],
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
def get_experiment_increments(request_data):
    
    expt_metric_name = request_data.metric_format_str.replace(
                                                        '{metric}', 
                                                        request_data.metric)
   
    expt_metric_name = expt_metric_name.replace(
        '{stat}', request_data.stat
    )
   
    time_valid_from = datetime.strftime(request_data.time_valid.start, 
                                        request_data.datetime_str)

    time_valid_to = datetime.strftime(request_data.time_valid.end, 
                                      request_data.datetime_str)
    request_dict = {'name': 'expt_metrics', 'method': 'GET',
                    'params': {'datestr_format': '%Y-%m-%d %H:%M:%S',
                               'filters':
                                 {'experiment':
                                   {'name': {
                                      'exact': request_data.experiment['name']['exact']},
                                    'wallclock_start':
                                      {'from': request_data.experiment['wallclock_start']['from'],
                                       'to': request_data.experiment['wallclock_start']['to']}},
                                  'metric_types': {'measurement_type': {'exact': [request_data.metric]},
                                                   'stat_type': {'exact': [request_data.stat]}},
                                  'regions': {'rgs_name': {'exact': ['global']}},
                                  'time_valid': {'from': time_valid_from,
                                                 'to': time_valid_to}},
                                 'ordering': [{'name': 'time_valid', 'order_by': 'asc'}]}}

    print(f'request_dict: {request_dict}')

    emr = ExptMetricRequest(request_dict)
    result = emr.submit()

    return result.details['records']

def build_base_figure():
    fig, ax = plt.subplots()
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tick_params(axis='x', which='both', bottom=False, top=False,
                    labelbottom=True)
    
    return(fig, ax)


def format_figure(ax, pa):
    '''
    ax.set_xlim([pa.axes_attrs.xmin, pa.axes_attrs.xmax])
    ax.set_ylim([pa.axes_attrs.ymin, pa.axes_attrs.ymax])
    plt.xticks(np.arange(pa.axes_attrs.xmin, (pa.axes_attrs.xmax + 1.e-6),
                         pa.axes_attrs.xint))
    '''
    ax.set_xlim([pd.Timestamp(plot_control_dict['date_range']['start']).timestamp(),
                 pd.Timestamp(plot_control_dict['date_range']['end']).timestamp()])
    ax.set_ylim([pa.axes_attrs.ymin, pa.axes_attrs.ymax])
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

def build_fig_dest(work_dir, fig_base_fn, stat, metric, date_range):
    
    start = datetime.strftime(date_range.start, '%Y%m%dT%HZ')
    end = datetime.strftime(date_range.end, '%Y%m%dT%HZ')
    dest_fn = fig_base_fn
    dest_fn += f'_{stat}_{metric}_{start}_to_{end}.png'
    
    dest_full_path = os.path.join(work_dir, dest_fn)
    
    parent_dir = pathlib.Path(dest_full_path).parent
    pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
    
    return dest_full_path

def save_figure(dest_full_path):
    print(f'saving figure to {dest_full_path}')
    plt.savefig(dest_full_path, dpi=600)

def plot_increments(experiments, stat, metric, metrics_df, work_dir, fig_base_fn,
                     date_range):

    if not isinstance(metrics_df, DataFrame):
        msg = 'Input data to plot_increments must be type pandas.DataFrame '\
            f'was actually type: {type(metrics_df)}'
        raise TypeError(msg)
    
    #plt_attr_key = f'{metric}'
    plt_attr_key = 'increment'
    pa = plot_attrs[plt_attr_key]
    (fig, ax) = build_base_figure()

    '''
    for expt in experiments:
        expt_name = expt.get('name')['exact']
    '''
    expt_name = experiments[0]['name']['exact']
    timestamps = list()
    labels = list()
    values = list()
    #for i, timestamp in enumerate(metrics_df['time_valid']):#metrics_to_show['cycle']:
    for row in metrics_df.itertuples():
        if row.time_valid.year == 2019:
            values.append(row.value)
            timestamps.append(row.time_valid.timestamp())
            labels.append('%02d-%02d' % (row.time_valid.month,
                                         row.time_valid.day,
                                          ))
    plt.bar(timestamps, values,
            #tick_label=labels,
            alpha=0.2,
            width=21600.,
            color=experiments[0]['graph_color'],
            #label=2019,#timestamp.year,
            #label=experiments[0]['graph_label']
            )
    plt.plot(timestamps, values, lw=0.5,#ls='None', marker='.',
             color=experiments[0]['graph_color'], label=2019)
    plt.title(expt_name)
    format_figure(ax, pa)
    fig_fn = build_fig_dest(work_dir, fig_base_fn, stat, metric, date_range)
    plt.ylabel('%s %s' % (stat, metric))
    
    all_labels = sorted(set(labels))
    label_spacing = len(all_labels)//10
    remainder = len(all_labels)%10
    #ipdb.set_trace()
    plt.xticks(ticks=np.linspace(sorted(set(timestamps))[0],
                                 sorted(set(timestamps))[-remainder-1],
                                 num=10),
               labels=sorted(set(labels))[:-remainder:label_spacing],
               rotation=30, ha='right')
    save_figure(fig_fn)

"""

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

"""

@dataclass
class PlotIncrementRequest(PlotInnovStatsRequest):
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
                for stat in stat_group.stats:
                    m_df = DataFrame()
                    for experiment in self.experiments:
                        request_data = RequestData(
                            self.datetime_str,
                            experiment,
                            stat_group.stat_group_frmt_str,
                            metric, stat,
                            self.date_range)
                        
                        e_df = get_experiment_increments(request_data)
                        e_df = e_df.sort_values(['time_valid', 'created_at'])
                        m_df = pd.concat([m_df, e_df], axis=0)

                    plot_increments(
                        self.experiments,
                        stat,
                        metric,
                        m_df,
                        self.work_dir,
                        self.fig_base_fn,
                        self.date_range)

if __name__=='__main__':
    plot_request = PlotIncrementRequest(plot_control_dict)
    plot_request.submit()
