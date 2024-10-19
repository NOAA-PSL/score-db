#!/usr/bin/env python

"""build GSI stats time series for plotting

usage: place this file in score-db/src, run using the python interpreter, i.e.

score-db/src$ python gsistats_timeseries.py

users shouldn't need to edit anything besides the run() function, which can
be customized according to their needs

This script uses a matplotlib styesheet. To make the style sheet available to
matplotlib, place the "agu_full.mplstyle" file in the "stylelib" direcotry under matplotlib.get_configdir(), which is usually either ~/.config/matplotlib/ or ~/.matplotlib/ (https://matplotlib.org/stable/users/explain/customizing.html#using-style-sheets)

for any questions, please feel free to contact Adam Schneider 
(Adam.Schneider@noaa.gov)
"""

import os
from datetime import datetime
import warnings

import numpy as np
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import colorcet as cc

from score_db import score_db_base

def run(make_plot=False, make_line_plot=True, select_array_metric_types=True,
        select_sat_name=True,
        experiment_list=['scout_run_v1',
                         'NASA_GEOSIT_GSISTATS'
                         #'scout_runs_gsi3dvar_1979stream'
                     ],
        array_metrics_list=['amsua_bias_post_corr_GSIstage_%',
                            #'amsua_std_%',
                            #'%_variance_%',
                            #'amsua_use_%'
                        ],
        sat_name = 'NOAA 15',
        start_date = '1979-01-01 00:00:00',
        stop_date = '2008-01-01 00:00:00'):
    """modify the above input variables to configure and generate time series
    data for various GSI related statistics
        
        experiment_list: list of experiments to plot in sequence
        array_metrics_list: list of metrics to plot in sequence
    """
    if make_plot or make_line_plot:
        plt.style.use('/Users/jknezha/.matplotlib/stylelib/agu_full.mplstyle')
    
    if not select_array_metric_types:
        array_metrics_list=['%_all_stats_%']
    
    for experiment_name in experiment_list:
        for array_metric_type in array_metrics_list:
            timeseries_data = GSIStatsTimeSeries(start_date, stop_date,
                            experiment_name=experiment_name, 
                            select_array_metric_types=select_array_metric_types,
                            array_metric_types=array_metric_type,
                            select_sat_name=select_sat_name,
                            sat_name=sat_name)
            timeseries_data.build(all_channel_max=False, # set max or mean
                                  all_channel_mean=False,
                                  by_channel=True) # other False

            if make_plot:
                timeseries_data.plot()
                plt.suptitle(experiment_name)
                #plt.show()
                metric_string = array_metric_type.split('%')[1] #this won't always work if you give a specific sensor value
                plt.savefig(os.path.join(
                                'results',
                                f'gsi{metric_string}{experiment_name}.png'),
                    dpi=600)
                plt.close()

            elif make_line_plot:
                stat_label = 'bias_post_corr_GSIstage_1'
                sensor_label = 'n15_amsua'
                timeseries_data.plot_line_plot(stat_label=stat_label, sensor_label=sensor_label)
                plt.suptitle(experiment_name)                #plt.show()
                metric_string = array_metric_type.split('%')[0] #again not expandable 
                plt.savefig(os.path.join(
                                #'results',
                                f'gsiline{metric_string}{experiment_name}.png'),
                    dpi=600)
                plt.close()
            else:
                timeseries_data.print_init_time()

#separate to be able to plot experiments on the same graphic/ doesn't work yet it's a thought
# def run_line_plot(make_line_plot=True, select_array_metric_types=True,
#         select_sat_name=True,
#         experiment_list=['scout_run_v1',
#                          'NASA_GEOSIT_GSISTATS'
#                          #'scout_runs_gsi3dvar_1979stream'
#                      ],
#         array_metrics_list=['amsua_bias_post_corr_GSIstage_%',
#                             #'amsua_std_%',
#                             #'%_variance_%',
#                             #'amsua_use_%'
#                         ],
#         sat_name = 'NOAA 15',
#         start_date = '1979-01-01 00:00:00',
#         stop_date = '2008-01-01 00:00:00'):
#     """modify the above input variables to configure and generate time series
#     data for various GSI related statistics
        
#         experiment_list: list of experiments to plot in sequence
#         array_metrics_list: list of metrics to plot in sequence
#     """
#     if make_line_plot:
#         plt.style.use('/Users/jknezha/.matplotlib/stylelib/agu_full.mplstyle')
    
#     if not select_array_metric_types:
#         array_metrics_list=['%_all_stats_%']
    
#     experiment_timeseries = dict()
#     for experiment_name in experiment_list:
#         for array_metric_type in array_metrics_list:
#             timeseries_data = GSIStatsTimeSeries(start_date, stop_date,
#                             experiment_name=experiment_name, 
#                             select_array_metric_types=select_array_metric_types,
#                             array_metric_types=array_metric_type,
#                             select_sat_name=select_sat_name,
#                             sat_name=sat_name)
#             timeseries_data.build(all_channel_max=False, # set max or mean
#                                   all_channel_mean=False,
#                                   by_channel=True) # other False
#             experiment_timeseries[experiment_name] = timeseries_data

#     if make_line_plot:
#         stat_label = 'amsua_bias_post_corr_GSIstage_1'
#         sensor_label = 'n15_amsua'

#         timeseries_data.plot_line_plot()
#         plt.suptitle(experiment_name)                #plt.show()
#         metric_string = array_metric_type.split('%')[0] #again not expandable 
#         plt.savefig(os.path.join(
#                         'results',
#                         f'gsiline{metric_string}{experiment_name}.png'),
#             dpi=600)
#         plt.close()
#     else:
#         timeseries_data.print_init_time()

class GSIStatsTimeSeries(object):
    def __init__(self, start_date, stop_date,
                 experiment_name = 'scout_run_v1',#
                                   #'scout_runs_gsi3dvar_1979stream',#
                select_array_metric_types = True,
                array_metric_types='%',
                select_sat_name = False,
                sat_name = None
                ):
        """Download metrics data for given experiment name
        """
        self.init_datetime = datetime.now()
        self.experiment_name = experiment_name
        self.select_array_metric_types = select_array_metric_types
        self.array_metric_types = array_metric_types
        self.select_sat_name = select_sat_name
        self.sat_name = sat_name
        self.get_data_frame(start_date, stop_date)

        
    def get_data_frame(self, start_date, stop_date):
        """request from the score-db application experiment data
        Database requests are submitted via score-db with a request dictionary
        """
        request_dict = {
            'db_request_name': 'expt_array_metrics',
            'method': 'GET',
            'params': {'filters':
                          {'experiment':{
                              'experiment_name':
                                  {'exact':
                                     self.experiment_name}
                                 },
                           'regions': {
                                            'name': {
                                                'exact': ['global']
                                            },
                                        },

                           'time_valid': {
                                            'from': start_date,
                                            'to': stop_date,
                                        },
                                    },
                       'ordering': [ {'name': 'time_valid', 'order_by': 'asc'}]
                   }
        
        }
    
        if self.select_array_metric_types:
            request_dict['params']['filters']['array_metric_types'] = {
                'name': {'like': self.array_metric_types}
            }

        if self.select_sat_name:
            request_dict['params']['filters']['sat_meta'] = {
                'sat_name': {'exact': self.sat_name}
            }

        db_action_response = score_db_base.handle_request(request_dict)    
        self.data_frame = db_action_response.details['records']
        
        # sort by timestamp, created at
        self.data_frame.sort_values(by=['metric_instrument_name',
                                        'sat_short_name',
                                        'time_valid',
                                        'created_at'], 
                                    inplace=True)
    
        # remove duplicate data
        self.data_frame.drop_duplicates(subset=['metric_name', 'time_valid'], 
                                        keep='last', inplace=True)
        
    def build(self, all_channel_max=True, all_channel_mean=False, by_channel=False):
        self.unique_stat_list = extract_unique_stats(
                                            set(self.data_frame['metric_name']))
        
        self.timestamp_dict = dict()
        self.timelabel_dict = dict()
        self.value_dict = dict()
        for i, stat_name in enumerate(self.unique_stat_list[0]):
            for j, gsi_stage in enumerate(self.unique_stat_list[1]):
                self.timestamp_dict[f'{stat_name}_GSIstage_{gsi_stage}'] = dict()
                self.timelabel_dict[f'{stat_name}_GSIstage_{gsi_stage}'] = dict()
                self.value_dict[f'{stat_name}_GSIstage_{gsi_stage}'] = dict()
                
        
        for key in self.value_dict.keys():
            for sat_short_name in set(self.data_frame.sat_short_name):
                for instrument_name in set(
                                    self.data_frame.metric_instrument_name):
                    sensor_label = f'{sat_short_name}_{instrument_name}'
                    
                    self.timestamp_dict[key][sensor_label] = list()
                    self.timelabel_dict[key][sensor_label] = list()
                    self.value_dict[key][sensor_label] = list()
        
        self.sensorlabel_dict = dict()
        yval = 0
        for row in self.data_frame.itertuples():
            metric_name_parts = row.metric_name.split('_')

            if metric_name_parts[0] == row.metric_instrument_name and metric_name_parts[-1] != 'None':
                stat_name = '_'.join(metric_name_parts[1:-2])
                gsi_stage = metric_name_parts[-1]
                
                stat_label = f'{stat_name}_GSIstage_{gsi_stage}'
                
                sensor_label = f'{row.sat_short_name}_{row.metric_instrument_name}'
                timestamp = row.time_valid#.timestamp()
                time_label = '%02d-%02d-%04d' % (row.time_valid.month,
                                             row.time_valid.day,
                                             row.time_valid.year,)
                
                if all_channel_mean and all_channel_max:
                    warnings.warn("got both channel mean and max, returning "
                                  "mean")
                    value = np.mean(row.value)
                elif all_channel_mean:
                    try:
                        value = np.mean(row.value)
                    except TypeError:
                        value = np.nan
                elif all_channel_max:
                    try:
                        value = np.max(row.value)
                    except TypeError:
                        value = np.nan
                elif by_channel: 
                    value = row.value

                
                #print(gsi_stage, stat_name, sensor_label, time_label, value)
                self.timestamp_dict[stat_label][sensor_label].append(timestamp)
                self.timelabel_dict[stat_label][sensor_label].append(time_label)
                self.value_dict[stat_label][sensor_label].append(value)
                
                if not sensor_label in self.sensorlabel_dict.keys():
                    self.sensorlabel_dict[sensor_label] = yval
                    yval -= 1
        
                #print(gsi_stage, stat_name, sensor_label, self.sensorlabel_dict[sensor_label])
        
    def plot(self, all_channel_mean=False, all_channel_max=True):
        """demonstrate how to plot metrics stored in a backened SQL database
        """
        cmap, boundaries, norm, tick_positions = get_colormap()
        fig, axes = plt.subplots(nrows = len(self.unique_stat_list[0]),
                                 ncols = len(self.unique_stat_list[1]),
                                 sharex=True, sharey=True,
                                 squeeze=False)
        
        ylabels = list()
        yvals = list()
        for sensor_label, yval in self.sensorlabel_dict.items():
            ylabels.append(sensor_label)
            yvals.append(yval)
                
        for row, stat_name in enumerate(self.unique_stat_list[0]):
            for col, gsi_stage in enumerate(self.unique_stat_list[1]):
                stat_label = f'{stat_name}_GSIstage_{gsi_stage}'
                
                if all_channel_mean:
                    axes[row, col].set_title(f'all channel mean {stat_name} (GSI stage {gsi_stage})')
                elif all_channel_max:
                    axes[row, col].set_title(f'all channel max {stat_name} (GSI stage {gsi_stage})')
                
                # y labels
                axes[row, col].set_yticks(np.array(yvals) - 0.5, 
                                          labels=ylabels, rotation=30, 
                                               va='center_baseline')
                axes[row, col].set_yticks(np.array(yvals), minor=True)
                axes[row, col].set_ylim(-len(yvals), 0)
                
                axes[row, col].grid(color='black', alpha=0.1, which='minor')
                
                # color mesh
                for sensor_label, yval in self.sensorlabel_dict.items():
                    values = self.value_dict[stat_label][sensor_label]
                    
                    # time dimension
                    timestamps = self.timestamp_dict[stat_label][sensor_label]
                    
                    try:
                        timestamps.append(timestamps[-1])
                        cax = axes[row, col].pcolormesh(np.array(timestamps),
                                                    np.array([yval, yval - 1]),
                                                    np.array([values]),
                                                    cmap=cmap,
                                                    norm=norm,
                                                    shading='flat')
                                                    
                        axes[row, col].xaxis.set_major_formatter(
                            mdates.ConciseDateFormatter(
                                      axes[row, col].xaxis.get_major_locator()))
                        axes[row, col].tick_params(which='major', labeltop=True,
                                                   labelright=False,
                                           top=True, right=False)
                        axes[row, col].tick_params(which='minor', left=False,
                                                   bottom=True, right=False,
                                                   top=True)
                
                    except IndexError:
                        warnings.warn(f'no data to plot for {stat_label} {sensor_label}')
                
                '''
                
                
                # Major ticks every half year, minor ticks every month,
                axes[row, col].xaxis.set_major_locator(
                                            mdates.MonthLocator(bymonth=(1, 7)))
                
                
                
                axes[row, col].xaxis.set_minor_locator(mdates.MonthLocator())
                axes[row, col].set_xlabel('cycle date (Gregorian)')
                for label in axes[row, col].get_xticklabels(which='major'):
                    label.set(rotation=30, horizontalalignment='right')
                '''
            
        # Add a colorbar to the plot with the same limits
        cbar = fig.colorbar(cax, ax=axes, orientation='horizontal',
                            #pad=0.1
                            boundaries=boundaries)
        cbar.set_label('temperature (K)')
        cbar.set_ticks(tick_positions)
        tick_labels = [f'{pos:.1f}' for pos in tick_positions]
        cbar.set_ticklabels(tick_labels)
    
    def print_init_time(self):
        print("GSIStatsTimeSeries object init date and time: ",
              f"{self.init_datetime}") 

    def plot_line_plot(self, stat_label, sensor_label, channels_to_plot=[4, 5, 6, 7]):
        """
        Plot time series for specified stat_label, sensor_label, and channels.
        
        Parameters:
        - stat_label: The specific stat label (string) to plot.
        - sensor_label: The specific sensor label (string) to plot.
        - channels_to_plot: List of channel indices to plot (default: channels 5-8). -1 for indexing, should read from the array labels in future 
        """
        
        # Prepare the plot
        plt.figure(figsize=(10, 6))

        # Loop through the specified channels
        for channel in channels_to_plot:
            try:
                # Extract the values for the specified stat_label and sensor_label
                channel_values = self.value_dict[stat_label][sensor_label]

                # Extract the corresponding timestamps
                timestamps = self.timestamp_dict[stat_label][sensor_label]

                # Ensure the channel index is valid and plot the values
                if len(channel_values) > channel:
                    plt.plot(timestamps, [v[channel] for v in channel_values], label=f'Channel {channel + 1}')
                else:
                    print(f"Channel {channel + 1} not found for {stat_label}, {sensor_label}")
                    
            except KeyError as e:
                print(f"Missing data for {stat_label}, {sensor_label}: {e}")

        # Add labels and title
        plt.xlabel('Timestamp')
        plt.ylabel('Value')
        plt.title(f'Channel Values vs Time for {sensor_label} ({stat_label})')
        plt.legend()

        # Rotate x-axis labels for readability
        plt.xticks(rotation=45)

        # Show the plot
        plt.tight_layout()
        #plt.show()




def get_colormap(cmap = cc.cm.CET_D1A, discrete_levels = 51, num_ticks=11,
                 vmin=-5, vmax=5):
    # Create discrete colormap
    colors = cmap(np.linspace(0, 1, discrete_levels))
    cmap_discrete = mcolors.ListedColormap(colors)

    # Create boundaries for the colormap
    boundaries = np.linspace(vmin, vmax, discrete_levels)
    norm = mcolors.BoundaryNorm(boundaries, cmap_discrete.N)
    
    # Adjust tick labels: Use fewer ticks
    tick_positions = np.linspace(vmin, vmax, num_ticks)
    
    return(cmap_discrete, boundaries, norm, tick_positions)
    
def extract_unique_stats(strings):
    # Create sets to store unique values in the second and last positions
    second_position_set = set()
    last_position_set = set()
    
    # Iterate over the set of strings
    for s in strings:
        parts = s.split('_')
        
        # Add the second and last elements to their respective sets
        if len(parts) > 1 and parts[-1] != 'None':  # Ensure there are at least 2 parts, 
            second_position_set.add('_'.join(parts[1:-2]))
            last_position_set.add(parts[-1])
    
    # Convert sets to sorted lists to maintain a consistent order
    second_position_list = sorted(list(second_position_set))
    last_position_list = sorted(list(last_position_set))
    
    # Combine the two lists into a 2D array (list of lists)
    unique_positions = [second_position_list, last_position_list]
    
    return unique_positions

def main():
    run()

if __name__=='__main__':
    main()