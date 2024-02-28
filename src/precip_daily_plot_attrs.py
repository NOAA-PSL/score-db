from collections import namedtuple

FIG_BASE_FN = 'precip_daily'
WORK_DIR =  '/contrib/Adam.Schneider/replay/results'

PlotAttrs = namedtuple('PlotAttrs', ['metric', 'axes_attrs', 'legend', 'xlabel',
                                     'ylabel'])

AxesAttrs = namedtuple('AxesAttrs', ['xmin', 'xmax', 'xint', 'ymin', 'ymax', 
                                     'yint'])

LegendData = namedtuple('LegendData', ['loc', 'fancybox', 'edgecolor', 
                                       'framealpha', 'shadow', 'fontsize',
                                       'facecolor'])

AxesLabel = namedtuple('AxesLabel', ['axis', 'label', 'horizontalalignment'])

DEFAULT_LEGEND_ATTRS = LegendData(loc='lower left', fancybox=None, 
                                  edgecolor=None, framealpha=None, shadow=None,
                                  fontsize='large', facecolor=None)

DEFAULT_XLABEL = AxesLabel(axis='x', label='Cycle date '
                                 '(Gregorian)', horizontalalignment='center')

plot_attrs = {'precip_daily': PlotAttrs(metric='precip_daily',
                                       axes_attrs=AxesAttrs(xmin=None,
                                                            xmax=None,
                                                            xint=None,
                                                            ymin=None,
                                                            ymax=None,
                                                            yint=None),
                                       legend=DEFAULT_LEGEND_ATTRS,
                                       xlabel=DEFAULT_XLABEL,
                                       ylabel=AxesLabel(
                                                   axis='y',
                                                   label='increment',
                                                   horizontalalignment='center'
                                                   ))}

plot_control_dict1 = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                     'end': '1999-01-01 00:00:00',
                                     'start': '1994-01-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{#'graph_color': 'black',
                                      #'graph_label': 'increments',
                                      'name': 'replay_stream1',
                                      'wallclock_start':'2023-07-08 16:25:57'}],
                     'fig_base_fn': FIG_BASE_FN,
                     'stat_groups': [{'cycles': [0,
                                                 #21600, 43200, 64800
                                                 ],
                                      'stats': ['daily_mean'],
                                      'metrics': ['mean_prateb_ave'],
                                      'stat_group_frmt_str':
                                          '{metric}'}],
                     'work_dir': WORK_DIR}

plot_control_dict2 = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                     'end': '2005-01-01 00:00:00',
                                     'start': '1999-01-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{#'graph_color': 'black',
                                      #'graph_label': 'increments',
                                      'name': 'replay_stream2',
                                      'wallclock_start':'2023-07-24 17:56:40'}],
                     'fig_base_fn': FIG_BASE_FN,
                     'stat_groups': [{'cycles': [0,
                                                 #21600, 43200, 64800
                                                 ],
                                      'stats': ['daily_mean'],
                                      'metrics': ['mean_prateb_ave'],
                                      'stat_group_frmt_str':
                                      '{metric}'}],
                     'work_dir': WORK_DIR}

plot_control_dict3 = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                     'end': '2010-01-01 00:00:00',
                                     'start': '2005-01-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{#'graph_color': 'black',
                                      #'graph_label': 'increments',
                                      'name': 'replay_stream3',
                                      'wallclock_start':'2023-01-22 09:22:05'}],
                     'fig_base_fn': FIG_BASE_FN,
                     'stat_groups': [{'cycles': [0,
                                                 #21600, 43200, 64800
                                                 ],
                                      'stats': ['daily_mean'],
                                      'metrics': ['mean_prateb_ave'],
                                      'stat_group_frmt_str':
                                      '{metric}'}],
                     'work_dir': WORK_DIR}

plot_control_dict4 = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                     'end': '2015-01-01 00:00:00',
                                     'start': '2010-01-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{#'graph_color': 'black',
                                      #'graph_label': 'increments',
                                      'name': 'replay_stream4',
                                      'wallclock_start':'2023-01-22 09:22:05'}],
                     'fig_base_fn': FIG_BASE_FN,
                     'stat_groups': [{'cycles': [0,
                                                 #21600, 43200, 64800
                                                 ],
                                      'stats': ['daily_mean'],
                                      'metrics': ['mean_prateb_ave'],
                                      'stat_group_frmt_str':
                                      '{metric}'}],
                     'work_dir': WORK_DIR}

plot_control_dict5 = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                     'end': '2020-01-01 00:00:00',
                                     'start': '2019-01-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{#'graph_color': 'black',
                                      #'graph_label': 'increments',
                                      'name': 'replay_stream5',
                                      'wallclock_start':'2023-07-08 06:20:22'}],
                     'fig_base_fn': FIG_BASE_FN,
                     'stat_groups': [{'cycles': [0,
                                                 # 21600, 43200, 64800
                                                 ],
                                      'stats': ['daily_mean'],
                                      'metrics': ['mean_prateb_ave', 'mean_soilm', 'mean_tmp2m'],
                                      'stat_group_frmt_str':
                                          '{metric}'}],
                     'work_dir': WORK_DIR}
plot_control_dict6 = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                    'end': '2021-01-01 00:00:00',
                                    'start': '2020-04-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{#'graph_color': 'black',
                                      #'graph_label': 'increments',
                                      'name': 'replay_stream6',
                                      'wallclock_start':'2023-07-24 20:29:23'}],
                     'fig_base_fn': FIG_BASE_FN,
                     'stat_groups': [{'cycles': [0,
                                                 # 21600, 43200, 64800
                                                 ],
                                      'stats': ['daily_mean'],
                                      'metrics': ['mean_prateb_ave', 'mean_soilm', 'mean_tmp2m'],
                                      'stat_group_frmt_str':
                                          '{metric}'}],
                     'work_dir': WORK_DIR}

plot_control_dict6_spinup = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                    'end': '2020-01-01 00:00:00',
                                    'start': '2019-01-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{#'graph_color': 'black',
                                      #'graph_label': 'increments',
                                      'name': 'replay_stream6_spinup',
                                      'wallclock_start':'2023-06-24 20:29:23'}],
                     'fig_base_fn': FIG_BASE_FN,
                     'stat_groups': [{'cycles': [0,
                                                 # 21600, 43200, 64800
                                                 ],
                                      'stats': ['daily_mean'],
                                      'metrics': ['mean_prateb_ave', 'mean_soilm', 'mean_tmp2m'],
                                      'stat_group_frmt_str':
                                          '{metric}'}],
                     'work_dir': WORK_DIR}

plot_control_dict5_overlap = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                    'end': '2021-01-01 00:00:00',
                                    'start': '2020-04-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{#'graph_color': 'black',
                                      #'graph_label': 'increments',
                                      'name': 'replay_stream5_overlap',
                                      'wallclock_start':'2023-08-08 06:20:22'}],
                     'fig_base_fn': FIG_BASE_FN,
                     'stat_groups': [{'cycles': [0,
                                                 # 21600, 43200, 64800
                                                 ],
                                      'stats': ['daily_mean'],
                                      'metrics': ['mean_prateb_ave','mean_soilm', 'mean_tmp2m'],
                                      'stat_group_frmt_str':
                                          '{metric}'}],
                     'work_dir': WORK_DIR}

plot_control_replay = {'date_range': {'datetime_str': '%Y-%m-%d %H:%M:%S',
                                    'end': '2000-01-01 00:00:00',
                                    'start': '1994-01-01 00:00:00'},
                     'db_request_name': 'expt_metrics',
                     'method': 'GET',
                     'experiments': [{#'graph_color': 'black',
                                      #'graph_label': 'increments',
                                      'name': 'gefsv13replay_0.25d_v0.1',
                                      'wallclock_start':'2023-07-24 18:13:14'}],
                     'fig_base_fn': FIG_BASE_FN,
                     'stat_groups': [{'cycles': [0,
                                                 # 21600, 43200, 64800
                                                 ],
                                      'stats': ['daily_mean'],
                                      'metrics': ['mean_prateb_ave', 'mean_ulwrf_avetoa'],
                                      'stat_group_frmt_str':
                                          '{metric}'}],
                     'work_dir': WORK_DIR}
