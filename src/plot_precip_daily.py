"""Copyright 2023 NOAA
All rights reserved.

Collection of methods to facilitate handling of score db requests
"""

import os
import pathlib
from dataclasses import dataclass, field
from collections import namedtuple
from datetime import datetime
from datetime import date

import numpy as np
import pandas as pd
from pandas import DataFrame
from matplotlib import pyplot as plt

from expt_metrics import ExptMetricRequest
from precip_daily_plot_attrs import plot_attrs
import precip_daily_plot_attrs
from plot_innov_stats import PlotInnovStatsRequest

RequestData = namedtuple('RequestData', ['datetime_str', 'experiment',
                                         'metric_format_str', 'metric',
                                         'stat',
                                         'time_valid'],)

def unique(sequence):
    seen = set()
    return [x for x in sequence if not (x in seen or seen.add(x))]

def get_experiment_precip(request_data):
    #expt_metric_name = request_data.metric_format_str.replace('{metric}', 
    #                                                    request_data.metric)
    metric_measurement_type = request_data.metric.replace('mean_', '')
    metric_measurement_type = metric_measurement_type.replace('std_', '')
    metric_measurement_name= request_data.metric

    stat_type = request_data.stat.replace('mean',
                                          '%s' % metric_measurement_name.split('_')[0])

    #expt_metric_name = expt_metric_name.replace(
    #    '{stat}', ''
    #)
   
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
                                  'metric_types': {'name': {'exact': [metric_measurement_name]},
                                                   'measurement_type': {'exact': [metric_measurement_type]},
                                                   'stat_type': {'exact': [stat_type]}},
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
    
    #ax.spines['top'].set_visible(False)
    #ax.spines['right'].set_visible(False)
    plt.tick_params(axis='both', which='both', bottom=True, top=True, left=True, right=True,
                    labelbottom=True, labelsize=3)
    
    return(fig, ax)


def format_figure(ax, pa, metric):
    '''
    ax.set_xlim([pa.axes_attrs.xmin, pa.axes_attrs.xmax])
    ax.set_ylim([pa.axes_attrs.ymin, pa.axes_attrs.ymax])
    plt.xticks(np.arange(pa.axes_attrs.xmin, (pa.axes_attrs.xmax + 1.e-6),
                         pa.axes_attrs.xint))
    '''
    ax.set_xlim([pd.Timestamp(plot_control_dict['date_range']['start']).timestamp(),
                 pd.Timestamp(plot_control_dict['date_range']['end']).timestamp()])
    
    if metric == 'mean_tmp2m':
        ax.set_ylim([260,#pa.axes_attrs.ymin,
                     310 #pa.axes_attrs.ymax
                     ])
    elif metric == 'mean_soilm':
        ax.set_ylim([0,#pa.axes_attrs.ymin,
                     1000 #pa.axes_attrs.ymax
                     ])
    elif metric == 'mean_prateb_ave':
        ax.set_ylim([0,#pa.axes_attrs.ymin,
                     10#pa.axes_attrs.ymax
                     ])
    plt.xlabel(xlabel=pa.xlabel.label,
               horizontalalignment=pa.xlabel.horizontalalignment)
    
    plt.ylabel(ylabel=pa.ylabel.label,
               horizontalalignment=pa.ylabel.horizontalalignment)
    
    '''
    plt.legend(loc=pa.legend.loc,
               fancybox=pa.legend.fancybox,
               edgecolor=pa.legend.edgecolor,
               framealpha=pa.legend.framealpha,
               shadow=pa.legend.shadow,
               facecolor=pa.legend.facecolor)
    '''
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

def plot_precip(experiments, stat, metric, metrics_df, metrics_df_std, work_dir, fig_base_fn,
                date_range):

    if not isinstance(metrics_df, DataFrame):
        msg = 'Input data to plot_increments must be type pandas.DataFrame '\
            f'was actually type: {type(metrics_df)}'
        raise TypeError(msg)
    
    #plt_attr_key = f'{metric}'
    plt_attr_key = 'precip_daily'
    pa = plot_attrs[plt_attr_key]
    (fig, ax) = build_base_figure()

    '''
    for expt in experiments:
        expt_name = expt.get('name')['exact']
    '''
    metrics_to_show = metrics_df.drop_duplicates(subset='time_valid', keep='last')
    std_to_show = metrics_df_std.drop_duplicates(subset='time_valid', keep='last')
    expt_name = experiments[0]['name']['exact']
    expt_graph_label = experiments[0]['graph_label']

    timestamps = list()
    labels = list()
    values = list()
    colors = list()
    cycle_labels = list()

    for row in metrics_to_show.itertuples():
        if row.time_valid >= date_range.start and row.time_valid < date_range.end:
            values.append(row.value)
            timestamps.append(row.time_valid.timestamp())
            labels.append('%02d-%02d-%04d' % (row.time_valid.month,
                                              row.time_valid.day,
                                              row.time_valid.year,
                                          ))
            cycle_labels.append('%dZ' % row.time_valid.hour)
            '''
            if row.time_valid.hour == 0:
                colors.append('lightcoral')
            elif row.time_valid.hour == 6:
                colors.append('yellowgreen')
            elif row.time_valid.hour == 12:
                colors.append('skyblue')
            elif row.time_valid.hour == 18:
                colors.append('orchid')
            '''
    values_std = np.zeros(len(timestamps))
    #for time_idx, timestamp in enumerate(timestamps):
    for row in std_to_show.itertuples():
        #std_timestamp = row.time_valid.timestamp()
        try:
            timestamp_index = timestamps.index(row.time_valid.timestamp())
            values_std[timestamp_index] = row.value
        except ValueError:
            print('Mean value missing for %s at %02d-%02d-%04d'
                  % (metric, row.time_valid.month, row.time_valid.day,
                     row.time_valid.year))
    
    if metric == 'mean_prateb_ave':
        values = 24 * 3600 * np.array(values) # convert to mm/s
        values_std = 24 * 3600 * np.array(values_std)
        units = 'mm/s'
    else:
        units = row.metric_unit
    myLabel = unique(cycle_labels) 
    '''
    plt.bar(timestamps, values,
            alpha=0.333,
            width=21600.*4, # 24 hours
            color='black')
    '''
    length = len(myLabel)
    '''
    for i in range(length):
        """ Plot the first unique cycles to format the legend
        """
        plt.errorbar(timestamps[i], values[i], yerr=values_std[i],
                     xerr=21600.*2, fmt='None', ls='None', 
                     color='black', alpha=0.333, label=cycle_labels[i])
    '''
    # proceed with onward
    plt.errorbar(timestamps, values, yerr=values_std, xerr=21600.*2,
                 ls='None', color='black', alpha=0.333)
   
    format_figure(ax, pa, metric)

    plt.title(stat+" "+metric+" " +expt_name, loc = "left")
    #today = date.today()
    #plt.title(today, loc = "right")
  
    plt.ylabel("%s" % units)

    fig_fn = build_fig_dest(work_dir, fig_base_fn, stat, metric, date_range)

    #create timestamps that are inorder for entire timeline (not limited to 1 year)
    timestamps_int = [int(timestamps) for timestamps in timestamps]
    all_monthly_labels = [datetime.fromtimestamp(timestamps_int).strftime('%m-%Y') for timestamps_int in timestamps_int]

    monthly_labels = unique(all_monthly_labels) 
    plt.xticks(ticks=np.arange(sorted(timestamps)[0],
                               sorted(timestamps)[-1],
                               60*60*24*(365.25/12.))[:len(monthly_labels)],
               labels=monthly_labels, rotation=45,ha='right',
               )
    plt.subplots_adjust(bottom=0.22)
    save_figure(fig_fn)

@dataclass
class PlotPrecipRequest(PlotInnovStatsRequest):
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
                    m_df_std = DataFrame()
                    for experiment in self.experiments:
                        request_data = RequestData(
                            self.datetime_str,
                            experiment,
                            stat_group.stat_group_frmt_str,
                            metric, stat,
                            self.date_range)
                        request_data_std = RequestData(
                            self.datetime_str,
                            experiment,
                            stat_group.stat_group_frmt_str,
                            metric.replace('mean', 'std'),
                            stat.replace('mean', 'std'),
                            self.date_range)
                        
                        try:
                            e_df = get_experiment_precip(request_data)
                            e_df_std = get_experiment_precip(request_data_std)
                            e_df = e_df.sort_values(['time_valid', 'created_at'])
                            e_df_std = e_df_std.sort_values(['time_valid', 'created_at'])
                            m_df = pd.concat([m_df, e_df], axis=0)
                            m_df_std = pd.concat([m_df_std, e_df_std], axis=0)
                            plot_yes = True
                        except KeyError:
                            print('no records found for %s %s, skipping' % (stat, metric))
                            plot_yes = False
                    if plot_yes:
                        plot_precip(
                            self.experiments,
                            stat,
                            metric,
                            m_df,
                            m_df_std,
                            self.work_dir,
                            self.fig_base_fn,
                            self.date_range)

if __name__=='__main__':
    for i, plot_control_dict in enumerate([#plot_control_dict1,
                                           #plot_control_dict2,
                                           #plot_control_dict3,
                                           #plot_control_dict4,
                             #precip_daily_plot_attrs.plot_control_dict5,
                             #precip_daily_plot_attrs.plot_control_dict5_overlap,
                             precip_daily_plot_attrs.plot_control_dict6_spinup,
                             precip_daily_plot_attrs.plot_control_dict6
                           ]):
        plot_request = PlotPrecipRequest(plot_control_dict)
        plot_request.submit()
