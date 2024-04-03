# score-db
Python package to manage the database backend to support the UFS-RNR workflow
experiment meta data and analyses data tracking and reporting.  The score-db
database uses the PostgreSQL database system which is hosted by AWS on an RDS
instance (currently administered by PSL).

Tools and utilities to catalogue and evaluate observation files.

# Installation and Environment Setup
1. Clone the score-db and score-hv repos.  Both of these repos are required.
score-db is responsible for managing the backend database which stores 
diagnostics data related to UFS-RNR experiments.  score-db has several APIs
to help users insert and collect data from the score-db database.  score-hv,
on the other hand, is responsible for harvesting data from the diagnostic

```sh
$ git clone https://github.com/noaa-psd/score-db.git
$ git clone https://github.com/noaa-psd/score-hv.git
```

2. Install or setup the UFS-RNR anaconda3 python environment and update it. 
If the UFS-RNR anaconda python environment is not already available, install
it now using the instructions found in the [UFS-RNR-stack](https://github.com/HenryWinterbottom-NOAA/UFS-RNR-stack.git) repo.  An example of the actual
installation script can be found at [scripts/build.UFS-RNR-stack.RDHPCS-Hera.anaconda3.sh](https://github.com/HenryWinterbottom-NOAA/UFS-RNR-stack/blob/0b0fd767928ebc56be0c1992b141015d9e3ff7a4/scripts/build.UFS-RNR-stack.RDHPCS-Hera.anaconda3.sh).
If you are installing this anaconda module at a different location than what
is configured in the above script, you will need to make modifications such
that the install location matches your desired location.  You will also need to
specify aws credentials for PSL's private s3 bucket.
3. Update the anaconda environment (follow anaconda update directions found [here](https://docs.anaconda.com/anaconda/install/update-version/) or use
the example shown below).  Note: if you do not specify the anaconda environment to
update, the `conda update --all` command will update the current environment. The
`--all` indicates that you want to update all packages.  In order to specify a
particular environment, use the command `conda update -n myenv --all`.

```sh
$ conda update conda
$ conda update --all
```

4. Load the anaconda3 environment
```sh
$ module purge
$ module use -a /contrib/home/builder/UFS-RNR-stack/modules
$ module load anaconda3
```
5. Make the python interpreter aware of where the score-db and score-hv
source code can be found.

```sh
$ export SCORE_DB_HOME_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
$ export PYTHONPATH=$SCORE_DB_HOME_DIR/src
$ export PYTHONPATH=$PYTHONPATH:[absolute or relative path to score-hv]/src
```

6. Configure the PostgreSQL credentials and settings for the score-db by
creating a `.env` file and by inserting the text shown below (note: this
text is taken straight from the file `.env_example`).  You will need to 
acquire the database password from the administrator (Sergey Frolov).

```
from the score-db repo top level, cat the example file
$ cat .env_example

SCORE_POSTGRESQL_DB_NAME = 'rnr_scores_db'
SCORE_POSTGRESQL_DB_PASSWORD = '[score_db_password]'
SCORE_POSTGRESQL_DB_USERNAME = 'ufsrnr_user'
SCORE_POSTGRESQL_DB_ENDPOINT = 'ufsrnr-pg-db.cmpwyouptct1.us-east-2.rds.amazonaws.com'
SCORE_POSTGRESQL_DB_PORT = 5432
```

# Using the APIs to Interact with score-db
Each of the APIs is structured in a similar way and are meant to be
accessible via either a direct library call or via a command line call
with a yaml file or a python dictionary as the only accepted arguments.

## Input values 
Every action made through the API requires a name and method. Valid methods are GET or PUT. The name must be a registered value in the db_request_regsitry. 
Currently valid registry options are:
```sh
'region' : 'Add or get regions'
'experiment' : 'Add, get, or update experiment registration data'
'expt_metrics' : 'Add or get experiment metrics data'
'metric_types' : 'Add, get, or update metric types'
'harvest_innov_stats' : 'Gather and store innovation statistics from diagnostics files'
'plot_innov_stats' : 'Plot innovation statistics'
'file_types' : 'Add, get, or update file types'
'storage_locations' : 'Add, get, or update storage locations'
'expt_file_counts' : 'Add or get experiment file counts'
'harvest_metrics' : 'Harvest and store metrics'
```

Example request dictionaries for each registry option are provided in the Appendix.

## Examples 
### How to Register an Experiment
This API helps the user register an experiment's meta data into the score-db
`experiments` table.

1. Setup the experiment registration yaml file.

example experiment registration yaml
```
---
name: experiment
method: PUT
body:
  name: EXAMPLE_EXPERIMENT_C96L64.UFSRNR.GSI_3DVAR.012016
  datestr_format: "%Y-%m-%d %H:%M:%S"
  cycle_start: '2016-01-01 00:00:00'
  cycle_stop: '2016-01-31 18:00:00'
  owner_id: first.last@noaa.gov
  group_id: gsienkf
  experiment_type: C96L64.UFSRNR.GSI_3DVAR.012016
  platform: pw_awv1
  wallclock_start: '2021-07-22 09:22:05'
  wallclock_end: '2021-07-24 05:31:14'
  description: '{"unstructured_json": "data"}'
```
2. Use the command line to execute the API and register the experiment.

```sh
$ python3 src/score_db_base.py tests/experiment_registration__valid.yaml
```

3. Call the experiment registration task from a python script.
```
import json
import experiments as expts
from experiments import ExperimentData, Experiment, ExperimentRequest

def register_experiment():
    with open(EXPERIMENT_CONFIG_FILE, 'r') as config_file:
        data=config_file.read()
    
    description = json.loads(data)

    request_dict = {
        'name': 'experiment',
        'method': 'PUT',
        'body': {
            'name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'datestr_format': '%Y-%m-%d %H:%M:%S',
            'cycle_start': '2016-01-01 00:00:00',
            'cycle_stop': '2016-01-31 18:00:00',
            'owner_id': 'Steve.Lawrence@noaa.gov',
            'group_id': 'gsienkf',
            'experiment_type': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'platform': 'pw_awv1',
            'wallclock_start': '2021-07-22 09:22:05',
            'wallclock_end': '2021-07-24 05:31:14',
            'description': json.dumps(description)
        }
    }

    er = ExperimentRequest(request_dict)
    response = er.submit()
    return response

response = register_experiment()
```

Note: the `EXPERIMENT_CONFIG_FILE` is meant to contain a json version of the
experiment configuration.  PostgreSQL allows searching through unstructured
JSON ([JSON Functions and Operators](https://www.postgresql.org/docs/12/functions-json.html) and [PostgreSQL JSON query tutorial](https://www.postgresqltutorial.com/postgresql-tutorial/postgresql-json/) should
help the user understand how to query data stored in the json `description`
column)

### How to Harvest Innovation Stats Produced by the UFS-RNR Workflow
This API will collect innovation statistics diagnostic data produced by the
UFS-RNR workflow.  This diagnostics data consists of bias, rmsd, and count
statistics of temperature, specific humidity, and uv wind and is stored in
netcdf files.  The harvester engine pulls this data out of the netcdf files
and inserts it into the score-db database.  The user must know the experiment
name and start wallclock time so that the API can associate the statistics
data with the correct registered experiment.  Note: the experiment must be
registered prior to any attempt to harvest the data.  Additionally, the netcdf
files must also already be downloaded and stored locally.


1. Setup the yaml input argument.

example of the input yaml (one can cut and paste this yaml data and)
```
date_range:
  datetime_str: '%Y-%m-%d %H:%M:%S'
  end: '2016-01-31 18:00:00'
  start: '2016-01-01 00:00:00'
db_request_name: harvest_innov_stats
expt_name: C96L64.UFSRNR.GSI_3DVAR.012016
expt_wallclk_strt: '2021-07-22 09:22:05'
files:
- cycles:
  - 0
  - 21600
  - 43200
  - 64800
  elevation_unit: plevs
  filename: innov_stats.metric.%Y%m%d%H.nc
  filepath: /home/slawrence/Development/experiment_data/uncoupled_c96_3dvar/gsi/
  harvester: innov_stats_netcdf
  metrics:
  - temperature
  - spechumid
  - uvwind
  stats:
  - bias
  - count
  - rmsd
output_format: tuples_list

```

2. Call the harvester engine on the command line (see below).  Both command
lines require mostly the same syntax `python3 src/score_db_base.py [command argument yaml]`
```sh
$ python3 src/score_db_base.py tests/netcdf_harvester_config__valid.yaml
```

or one could issue the command from within a python script.
```sh
from harvest_innov_stats import HarvestInnovStatsRequest

harvester_control_dict = {
  "date_range": {
    "datetime_str": "%Y-%m-%d %H:%M:%S",
    "end": "2016-01-31 18:00:00",
    "start": "2016-01-01 00:00:00"
  },
  "db_request_name": "harvest_innov_stats",
  "expt_name": "C96L64.UFSRNR.GSI_3DVAR.012016",
  "expt_wallclk_strt": "2021-07-22 09:22:05",
  "files": [
    {
      "cycles": [
        0,
        21600,
        43200,
        64800
      ],
      "elevation_unit": "plevs",
      "filename": "innov_stats.metric.%Y%m%d%H.nc",
      "filepath": "/home/slawrence/Development/experiment_data/uncoupled_c96_3dvar/gsi/",
      "harvester": "innov_stats_netcdf",
      "metrics": [
        "temperature",
        "spechumid",
        "uvwind"
      ],
      "stats": [
        "bias",
        "count",
        "rmsd"
      ]
    }
  ],
  "output_format": "tuples_list"
}

hc = HarvestInnovStatsRequest(harvester_control_dict)
hc.submit()
```

### How to Plot Innovation Statistics
This API will collect innovation statistics produced by one or more UFS-RNR
experiments.  The statistics must already be inserted into the `expt_metrics`
table and the experiments must already be registered.

1. Setup the yaml input argument.

example of the input yaml (one can cut and paste this yaml data and)
```
date_range:
  datetime_str: '%Y-%m-%d %H:%M:%S'
  end: '2016-01-31 18:00:00'
  start: '2016-01-01 00:00:00'
db_request_name: plot_innov_stats
experiments:
- graph_color: blue
  graph_label: C96L64 GSI Uncoupled 3DVAR Experiment
  name: C96L64.UFSRNR.GSI_3DVAR.012016
  wallclock_start: '2021-07-22 09:22:05'
- graph_color: red
  graph_label: C96L64 GSI and SOCA Coupled 3DVAR Experiment
  name: C96L64.UFSRNR.GSI_SOCA_3DVAR.012016
  wallclock_start: '2021-07-24 11:31:16'
fig_base_fn: C96L64_GSI_3DVAR_VS_GSI_SOCA_3DVAR
stat_groups:
- cycles:
  - 0
  - 21600
  - 43200
  - 64800
  elevation_unit: plevs
  metrics:
  - temperature
  - spechumid
  - uvwind
  regions:
  - equatorial
  - global
  - north_hemis
  - south_hemis
  - tropics
  stat_group_frmt_str: innov_stats_{metric}_{stat}
  stats:
  - bias
  - rmsd
work_dir: /absolute/path/to/desired/figure/location
```

2. Call the harvester engine on the command line (see below).  Both command
lines require mostly the same syntax `python3 src/score_db_base.py [command argument yaml]`
```sh
$ python3 src/score_db_base.py tests/plot_innov_stats_config__valid.yaml
```

or one could issue the command from within a python script.
```
from plot_innov_stats import PlotInnovStatsRequest

def plot_innov_stats_for_date_range():

    plot_control_dict = {
        'db_request_name': 'plot_innov_stats',
        'date_range': {
            'datetime_str': '%Y-%m-%d %H:%M:%S',
            'start': '2016-01-01 00:00:00',
            'end': '2016-01-31 18:00:00'
        },
        'experiments': [
            {
                'name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
                'wallclock_start': '2021-07-22 09:22:05',
                'graph_label': 'C96L64 GSI Uncoupled 3DVAR Experiment',
                'graph_color': 'blue'
            },
            {
                'name': 'C96L64.UFSRNR.GSI_SOCA_3DVAR.012016',
                'wallclock_start':  '2021-07-24 11:31:16',
                'graph_label': 'C96L64 GSI and SOCA Coupled 3DVAR Experiment',
                'graph_color': 'red'
            }
        ],
        'stat_groups': [
            {
                'cycles': CYCLES,
                'stat_group_frmt_str': 'innov_stats_{metric}_{stat}',
                'metrics': ['temperature','spechumid','uvwind'],
                'stats': ['bias', 'rmsd'],
                'elevation_unit': 'plevs',
                'regions': [
                    'equatorial',
                    'global',
                    'north_hemis',
                    'south_hemis',
                    'tropics'
                ]
            }
        ],
        'work_dir': '/absolute/path/to/desired/figure/location',
        'fig_base_fn': 'C96L64_GSI_3DVAR_VS_GSI_SOCA_3DVAR'
    }

    plot_request = PlotInnovStatsRequest(plot_control_dict)
    plot_request.submit()

plot_innov_stats_for_date_range()
```

# Appendix

## Table Schemas

The score-db backend package is comprised of four tables and several APIs
which are meant to help the user insert and select data from the score-db
database.  Instructions for API use are shown below.  This section describes
what information is stored in each table.  
`cmd_results`.


```sh
experiments

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    cycle_start = Column(DateTime, nullable=False)
    cycle_stop = Column(DateTime, nullable=False)
    owner_id = Column(String(64), nullable=False)
    group_id = Column(String(16))
    experiment_type = Column(String(64))
    platform = Column(String(16), nullable=False)
    wallclock_start = Column(DateTime, nullable=False)
    wallclock_end = Column(DateTime)
    description = Column(JSONB(astext_type=sa.Text()), nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

```sh
regions

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(79), nullable=False)
    bounds = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)

    metrics = relationship('ExperimentMetric', back_populates='region')
```

```sh
metric_types

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    long_name = Column(String(128))
    measurement_type = Column(String(64), nullable=False)
    measurement_units = Column(String(64))
    stat_type = Column(String(64))
    description = Column(JSONB(astext_type=sa.Text()), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    
    metrics = relationship('ExperimentMetric', back_populates='metric_type')
```

```sh
expt_metrics

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id'))
    metric_type_id = Column(Integer, ForeignKey('metric_types.id'))
    region_id = Column(Integer, ForeignKey('regions.id'))
    elevation = Column(Float, nullable=False)
    elevation_unit = Column(String(32))
    value = Column(Float)
    time_valid = Column(DateTime, nullable=False)
    forecast_hour = Column(Float)
    ensemble_member = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow())

    experiment = relationship('Experiment', back_populates='metrics')
    metric_type = relationship('MetricType', back_populates='metrics')
    region = relationship('Region', back_populates='metrics')
```
```sh
storage_locations

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    platform = Column(String(128), nullable=False)   
    bucket_name = Column(String(128), nullable=False)
    key = Column(String(128))
    platform_region = Column(String(64))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    file_counts = relationship('ExptStoredFileCount' back_populates='storage_location')
```

```sh
file_types

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    file_template = Column(String(64), nullable=False)
    file_format = Column(String(64))
    description = Column(JSONB(astext_type=sa.Text()), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    
    file_counts = relationship('ExptStoredFileCount', back_populates='file_type')
```

```sh
expt_stored_file_counts

    id = Column(Integer, primary_key=True, autoincrement=True)
    storage_location_id = Column(Integer, ForeignKey('storage_locations.id'))
    file_type_id = Column(Integer, ForeignKey('file_types.id'))
    experiment_id = Column(Integer, ForeignKey('experiments.id'))
    count = Column(Float, nullable=False)
    folder_path = Column(String(255))
    cycle = Column(DateTime)
    time_valid = Column(DateTime)
    forecast_hour = Column(Float)
    file_size_bytes = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow())

    experiment = relationship('Experiment', back_populates='file_counts')
    file_type = relationship('FileType', back_populates='file_counts')
    storage_location = relationship('StorageLocation', back_populates='file_counts')
```

```sh
expt_array_metrics

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id'))
    array_metric_type_id = Column(Integer, ForeignKey('array_metric_types.id'))
    region_id = Column(Integer, ForeignKey('regions.id'))
    value = Column(ARRAY(Float))
    bias_correction = Column(ARRAY(Float))
    assimilated = Column(Boolean)
    time_valid = Column(DateTime)
    forecast_hour = Column(Float)
    ensemble_member = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow())

    experiment = relationship('Experiment', back_populates='array_metrics')
    array_metric_type = relationship('ArrayMetricType', back_populates='array_metrics')
    region = relationship('Region', back_populates='array_metrics')
```

```sh
array_metric_types

    id = Column(Integer, primary_key=True, autoincrement=True)
    sat_meta_id = Column(Integer, ForeignKey('sat_meta.id'), nullable=True)
    obs_platform = Column(String(128))
    name = Column(String(128), nullable=False)
    long_name = Column(String(128))
    measurement_type = Column(String(64), nullable=False)
    measurement_units = Column(String(64))
    stat_type = Column(String(64))
    array_coord_labels = Column(ARRAY(String))
    array_coord_units = Column(ARRAY(String))
    array_index_values = Column(ARRAY(String))
    array_dimensions = Column(ARRAY(String))
    description = Column(JSONB(astext_type=sa.Text()), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)

    array_metrics = relationship('ExptArrayMetric', back_populates='array_metric_type')
    sat_meta = relationship('SatMeta', back_populates='array_metric_type')  
```

```sh
sat_meta

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256))
    sat_id = Column(Integer)
    sat_name = Column(String(128))
    sensor = Column(String(64))
    channel = Column(String(64))
    scan_angle = Column(String(64))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime) 

    array_metric_type = relationship('ArrayMetricType', back_populates='sat_meta')
```

## Request Dictionaries / YAML Formats

All requests require either a dictionary or a YAML file to configure the call to the database. GET calls, e.g., are requests to download subsets of data using filters that are specified with a nested dictionary or within a YAML file configuration hierarchy. PUT calls must similarly (via defining a key:value structured hierarchy) specify which data to upload to the database. Other calls must also be configured with a dictionary or YAML file. The following example configuration dictionaries (which could be similarly defined in a YAML file with the same hierarchy) are provided as templates for basic use cases.

### Experiment Dictionaries
Example format of request dictionaries for 'experiment' calls.

GET: 

```sh
request_dict = {
        'name': 'experiment',
        'method': 'GET',
        'params': {
            'filters': {
                'name': {
                    'exact': 'C96L64.UFSRNR.GSI_SOCA_3DVAR.012016'
                },
                'cycle_start': {
                    'from': '2015-01-01 00:00:00',
                    'to': '2018-01-01 00:00:00'
                },
                'cycle_stop': {
                    'from': '2015-01-01 00:00:00',
                    'to': '2018-01-01 00:00:00'
                },
                'owner_id': {
                    'exact': 'first.last@noaa.gov'
                },
                'experiment_type': {
                    'like': '%COUPLED%'
                },
                'platform': {
                    'exact': 'pw_awv1'
                },
                'wallclock_start': {
                    'from': '2022-01-01 00:00:00',
                    'to': '2022-07-01 00:00:00'
                },

            },
            'ordering': [
                {'name': 'group_id', 'order_by': 'desc'},
                {'name': 'created_at', 'order_by': 'desc'}
            ],
            'record_limit': 4
        }
    }
```

PUT:
```sh
request_dict = {
        'name': 'experiment',
        'method': 'PUT',
        'body': {
            'name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'datestr_format': '%Y-%m-%d %H:%M:%S',
            'cycle_start': '2016-01-01 00:00:00',
            'cycle_stop': '2016-01-31 18:00:00',
            'owner_id': 'first.last@noaa.gov',
            'group_id': 'gsienkf',
            'experiment_type': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'platform': 'pw_awv1',
            'wallclock_start': '2021-07-22 09:22:05',
            'wallclock_end': '2021-07-24 05:31:14',
            'description': #JSON VALUE OF DESCRIPTION
        }
    }
```
Values which can be null or not provided: group_id, experiment_type, wallclock_end, description

### Experiment Metric Dictionaries
Example format of request dictionaries for 'expt_metrics' calls.

GET:

```sh
request_dict = {
        'name': 'expt_metrics',
        'method': 'GET',
        'params': {
            'datestr_format': '%Y-%m-%d %H:%M:%S',
            'filters': {
                'experiment': {
                    'name': {
                        'exact': 'UFSRNR_GSI_SOCA_3DVAR_COUPLED_122015_HC44RS_lstr_tst',
                    },
                    'wallclock_start': {
                        'from': '2022-08-03 02:00:00',
                        'to': '2022-08-03 06:00:00'
                    }
                },
                'metric_types': {
                    'name': {
                        'exact': ['innov_stats_temperature_rmsd']
                    },
                    'stat_type': {
                        'exact': ['rmsd']
                    }
                },
                'regions': {
                    'name': {
                        'exact': ['global']
                    },
                },

                'time_valid': {
                    'from': '2015-01-01 00:00:00',
                    'to': '2016-01-03 00:00:00',
                },
            },
            'ordering': [
                {'name': 'time_valid', 'order_by': 'asc'}
            ]
        }
    }
```    

PUT:
```sh
request_dict = {
        'db_request_name' : 'expt_metrics',
        'method': 'PUT',
        'body' : {
            'expt_name': experiment_name,
            'expt_wallclock_start': experiment_wallclock,
            'metrics': {
                'name': name,
                'region_name': region,
                'elevation': elevation,
                'elevation_unit': elevation_unit,
                'value': value,
                'time_valid': time_valid,
                'forecast_hour' : forecast_hour,
                'ensemble_member' : ensemble_member
            },
            'datestr_format': '%Y-%m-%d %H:%M:%S',
        }
    }
```
Values which can be null or not provided: elevation_unit, forecast_hour, ensemble_member

Note: for a successful PUT call, the experiment, region, and metric type referenced in the body must already be registered using the score_db_base.py. See the first example above on How To Register an Experiment. The process is the same for the other data types. 

### Harvest Metrics Dictionary 
Harvest metrics only accepts PUT calls, therefore a method is not required. Any GET call for metrics should be through 'expt_metrics'. 

```sh
request_dict = {
        'db_request_name' : 'harvest_metrics',
        'body' : {
            'expt_name': experiment_name,
            'expt_wallclock_start': experiment_wallclock,
            'datestr_format': '%Y-%m-%d %H:%M:%S',
        },
        'hv_translator': hv_translator,
        'harvest_config': #Dictionary configuration for harvest
    }
```

Note the format of 'harvest_config' is required to be a valid config for 
score-hv calls. 'hv_translator' needs to be a string value for a registered harvester translator in the hv_translator_registry.py. 

### Harvest Innov Stats Dictionary
Harvest innov stats only accepts PUT calls, therefore a method is not required. Any GET call for metrics should be through 'expt_metrics'.

```sh
request_dict = {
        'db_request_name': 'harvest_innov_stats',
        'date_range': {
            'datetime_str': '%Y-%m-%d %H:%M:%S',
            'start': '2015-12-01 0:00:00',
            'end': '2015-12-01 0:00:00'
        },
        'files': [
            {
                'filepath': 'path/to/file/to/harvest',
                'filename': 'innov_stats.metric.%Y%m%d%H.nc',
                'cycles': CYCLES,
                'harvester': 'innov_stats_netcdf',
                'metrics': ['temperature','spechumid','uvwind'],
                'stats': ['bias', 'count', 'rmsd'],
                'elevation_unit': 'plevs'
            },
        ],
        'output_format': 'tuples_list'
    }
```

### Metric Types Dictionaries
Example format of request dictionaries for 'metric_types' calls.

GET: 
```sh
request_dict = {
        'name': 'metric_type',
        'method': 'GET',
        'params': {
            'filters': {
                'name': {
                    'exact': 'innov_stats_temperature_rmsd',
                    'in': ['innov_stats_temperature_rmsd', 'innov_stats_uvwind_rmsd']
                },
                'measurement_type': {
                    'exact': 'temperature'
                },
                'measurement_unit': {
                    'like': 'celsius'
                },
                'stat_type': {
                    'exact': 'rmsd'
                },
                'long_name': {
                    'exact': 'rmsd of innov stats temperature'
                }
            },
            'ordering': [
                {'name': 'name', 'order_by': 'desc'},
                {'name': 'created_at', 'order_by': 'desc'}
            ],
            'record_limit': 4
        }
    }
```

PUT:
```sh
request_types = {
        'db_request_name' : 'metric_types',
        'method': 'PUT',
        'body' : {
            'name': name,
            'long_name': long_name,
            'measurement_type': measurement_type,
            'measurement_units': units,
            'stat_type': stat_type,
            'description': #JSON FORMAT OF DESCRIPTION
        }
    }
```

Values which can be null or not provided: measurement_units, stat_type, description

### Regions Dictionaries
Example format of request dictionary for 'regions' calls.

GET:
```sh
request_dict = {
        'name': 'region',
        'method': 'GET',
        'params': {'filter_type': 'by_name'},
        'body': {
            'regions': [
                'global',
                'equatorial',
            ]
        }
    }
```

PUT:
```sh
request_dict = {
        'name': 'region',
        'method': 'PUT',
        'body': {
            'regions': [
                {'name': 'global', 'min_lat': -90.0, 'max_lat': 90.0, 'east_lon': 0.0, 'west_lon': 360.0},
                {'name': 'equatorial', 'min_lat': -5.0, 'max_lat': 5.0, 'east_lon': 0.0, 'west_lon': 360.0},
            ]
        }
    }
```


### Storage Location Dictionaries 
Example format of request dictionary for 'storage_locations' calls.

GET:
```sh
request_dict = {
        'name': 'storage_locations',
        'method': 'GET',
        'params': {
            'datestr_format': '%Y-%m-%d %H:%M:%S',
            'filters': {
                'name': {
                    'exact': 's3_example_bucket'
                },
            }
        }
    }
```

PUT:
```sh
request_dict = {
        'name': 'storage_locations',
        'method': 'PUT',
        'body': {
            'name': 's3_example_bucket',
            'platform': 'aws_s3', 
            'bucket_name': 'noaa-example-score-db-bucket',
            'key': 'reanalysis',
            'platform_region': 'n/a'
        }
    }
```

Values which can be null or not provided: key, platform_region

### File Types Dictionaries
Example request dictionaries for the 'file_types' calls.

GET:
```sh
request_dict = {
        'name': 'file_types',
        'method': 'GET',
        'params' : {
            'filters': {
                'name' :{
                    'exact' : 'example_type'
                }
            }
        }
    }
```

PUT:
```sh
request_dict = {
        'name': 'file_types',
        'method' : 'PUT',
        'body' :{
            'name': 'example_type',
            'file_template': '*.example',
            'file_format': 'text',
            'description': json.dumps({"name": "example"})
        }
    }
```
Values which can be null or not provided: file_format, description

### Experiment File Counts Dictionaries
Example request dictionaries for the 'expt_file_counts' calls. 

GET:
```sh
request_dict = {
        'name' : 'expt_file_counts',
        'method': 'GET',
        'params' : {
            'filters': {
                'experiment': {
                    'experiment_name': {
                        'exact': 'C96L64.UFSRNR.GSI_3DVAR.012016'
                    }
                },
                'file_types': {
                    'file_type_name': {
                        'exact': 'example_type',
                    },
                },
                'storage_locations': {
                    'storage_loc_name' :{
                        'exact': 's3_example_bucket',
                    },
                },
            }
        }
    }
```

PUT:
```sh
  request_dict = {
        'name': 'expt_file_counts',
        'method': 'PUT',
        'body': {
            'experiment_name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'wallclock_start': '2021-07-22 09:22:05',
            'file_type_name': 'example_type',
            'file_extension': '.example',
            'time_valid': '2023-02-05 06:00:00',
            'forecast_hour' : 120,
            'file_size_bytes' : 1234567890,
            'bucket_name' : 'noaa-example-score-db-bucket',
            'platform': 'aws_s3',
            'key': 'reanalysis',
            'count': 1230,
            'folder_path': 'noaa-example-score-db-bucket/reanalysis/2023/02/23/2023022306',
            'cycle': '2023-02-03 06:00:00'
        }
    }
```
Values which can be null or not provided: folder_path, cycle, time_valid, forecast_hour, file_size_bytes

Note: the associated experiment, file type, and storage locations referenced in the body values must already be registered for a successful file count PUT call  using the score_db_base.py. See the first example above on How To Register an Experiment. The process is the same for the other data types. 

### Sat Meta Dictionaries
Example dictionaries for 'sat_meta' calls. 

GET:
```sh
request_dict = {
        'name': 'sat_meta',
        'method': 'GET',
        'params' : {
            'filters': {
                'name' :{
                    'exact' : 'example_sat_meta'
                }
            }
        }
    }
```

PUT:
```sh
request_dict = {
        'name': 'sat_meta',
        'method' : 'PUT',
        'body' :{
            'name': 'example_sat_meta',
            'sat_id': 123456789,
            'sat_name': 'Example Sat Name',
            'sensor': 'examplesensor',
            'channel': '1',
            'scan_angle':'90 degreees sectors fore- and aft-'
        }
    }
```
Each value can be null as necessary. A unique sat meta is considered the combination of sat_name, sat_id, sensor, channel, and scan_angle. 

### Array Metric Type Dictionaries
Example dictionaries for 'array_metric_types' calls.

GET:
```sh
    request_dict = {
        'name': 'array_metric_types',
        'method':'GET',
        'params':{
            'filters':{
                'name':{
                    'exact':'vertical_example_metric'
                },
                'sat_meta_name':{
                    'exact': 'example_sat_meta'
                },
                'stat_type':{
                    'exact':'example_stat'
                }
            },
            'limit':1
        }
    }
```
To search based on sat_meta values, add the sat_meta in front of the value to filter on. 

PUT:
```sh
request_dict = {
        'name': 'array_metric_types',
        'method': 'PUT',
        'body': {
            'name': 'vertical_example_metric',
            'longname': 'vertical long name example',
            'obs_platform': 'satellite',
            'measurement_type': 'example_measurement_type',
            'measurement_units': 'example_measurement_units',
            'stat_type': 'example_stat',
            'array_coord_labels': ['temperature', 'elevation'],
            'array_coord_units': ['K', 'feet'],
            'array_index_values': [[10, 20, 30],[1000, 5000, 10000]],
            'array_dimensions': [3, 3],
            'description': json.dumps("example array metric type for testing purposes"),
            'sat_meta_name': 'example_sat_meta',
            'sat_id': 123456789,
            'sat_name': 'Example Sat Name',
            'sat_sensor':'examplesensor',
            'sat_channel':'1'
        }
    }
```
The 'sat' values are only required when obs_platform is satellite to associate the appropriate sat_meta value to the type. The sat_meta value must be pre-registered before registering the array metric type. 

### Experiment Array Metric Type Dictionaries
Example dictionaries for 'expt_array_metrics' calls.

GET:
```sh
request_dict = {
        'name': 'expt_array_metrics',
        'method': 'GET',
        'params': {
            'datestr_format': '%Y-%m-%d %H:%M:%S',
            'filters': {
                'experiment': {
                    'name': {
                        'exact': 'C96L64.UFSRNR.GSI_3DVAR.012016',
                    },
                    'wallclock_start': {
                        'from': '2021-07-22 02:22:05',
                        'to': '2021-07-22 10:22:05'
                    }
                },
                'metric_types': {
                    'name': {
                        'exact': ['vertical_example_metric']
                    },
                },
                'regions': {
                    'name': {
                        'exact': ['global']
                    },
                },

                'time_valid': {
                    'from': '2015-01-01 00:00:00',
                    'to': '2016-01-03 00:00:00',
                },
            },
            'ordering': [
                {'name': 'time_valid', 'order_by': 'asc'}
            ]
        }
    }
```

PUT:
```sh
request_dict = {
        'name': 'expt_array_metrics',
        'method': 'PUT',
        'body': {
            'expt_name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
            'expt_wallclock_start': '2021-07-22 09:22:05',
            'array_metrics': [
                ExptArrayMetricInputData('vertical_example_metric','global',[[1, 2, 3],[4, 5, 6],[7, 8, 9]], [[0, 1, 0],[1, 0, 1],[0, 0, 1]], True, '2015-12-02 06:00:00', None, None),
                ExptArrayMetricInputData('vertical_example_metric2','global',[[111, 222, 333],[444, 555, 666],[777, 888, 999]], [[1, 1, 0],[1, 0, 1],[1, 0, 0]], True, '2015-12-02 18:00:00', 24, 12)
            ],
            'datestr_format': '%Y-%m-%d %H:%M:%S'
        }
    }
```
Multiple array metrics can be provided as a list at one time as seen in this example.

Note: the associated array metric type, provided via the name, must be pre-registered for a successful put call.

### Plot Innovation Stats Dictionary
Example request dictionary of a call to 'plot_innov_stats'.

```sh
plot_control_dict = {
        'db_request_name': 'plot_innov_stats',
        'date_range': {
            'datetime_str': '%Y-%m-%d %H:%M:%S',
            'start': '2016-01-01 00:00:00',
            'end': '2016-01-31 18:00:00'
        },
        'experiments': [
            {
                'name': 'C96L64.UFSRNR.GSI_3DVAR.012016',
                'wallclock_start': '2021-07-22 09:22:05',
                'graph_label': 'C96L64 GSI Uncoupled 3DVAR Experiment',
                'graph_color': 'blue'
            },
            {
                'name': 'C96L64.UFSRNR.GSI_SOCA_3DVAR.012016',
                'wallclock_start':  '2021-07-24 11:31:16',
                'graph_label': 'C96L64 GSI and SOCA Coupled 3DVAR Experiment',
                'graph_color': 'red'
            }
        ],
        'stat_groups': [
            {
                'cycles': CYCLES,
                'stat_group_frmt_str': 'innov_stats_{metric}_{stat}',
                'metrics': ['temperature','spechumid','uvwind'],
                'stats': ['bias', 'rmsd'],
                'elevation_unit': 'plevs',
                'regions': [
                    'equatorial',
                    'global',
                    'north_hemis',
                    'south_hemis',
                    'tropics'
                ]
            }
        ],
        'work_dir': '/absolute/path/to/desired/figure/location',
        'fig_base_fn': 'C96L64_GSI_3DVAR_VS_GSI_SOCA_3DVAR'
    }
```

## Code Structure

The code base is structured using separate files to handle interactions for separate tables as well as extra functionalities, i.e., harvester interactions. All of the code functionality resides with in the **src** folder. 

The main file is *score_db_base.py* which is the launch point for all calls made via command line or outside script. This file contains the code which parses the input yaml or dictionary into a useful dictionary format and assigns the call to the appropriate registry item. 

The *db_request_registry.py* contains the registration for all valid 'name' values for inputs. The registry is used to direct the call to the correct set of code and table interactions, i.e. experiments vs storage_locations. 

The *db_utils.py*, *time_utils.py*, *file_utils.py* and *yaml_utils.py* files contains utility functions that are referenced frequently throughout the code base for their respective topics (database interactions, handling datetimes, files, and yaml format files).

The *db_action_response.py* file defines the response code structure that is expected by all return calls for values called via the registry. 

The *score_table_models.py* file defines all the of the tables in the database using SQLAlchemy and contains the code to build those repsective tables. 

Majority of the files are used for calls to manipulate specific database tables. The relationship between those files and the tables is as follows: 

- experiments: *experiments.py*
- regions: *regions.py*
- metric_types: *metric_types.py*
- expt_metrics: *expt_metrics.py*
- storage_locations: *storage_locations.py*
- file_types: *file_types.py*
- expt_stored_file_counts: *expt_file_counts.py*
- sat_meta: *sat_meta.py*
- array_metric_types: *array_metric_types.py*
- expt_array_mterics: *expt_array_metrics.py*

The general purpose of all of these files is to define a code structure based on the columns of the database, handle the processing of input data into the appropriate values, handle any input filters or order_by statements for GET calls, and finally to handle the GET and PUT calls using SQLAlchemy to input or retrieve data from the database. 

The *expt_metrics.py*, *expt_file_counts.py*, and *expt_array_metrics.py* files have interactions with the other files for the relevant tables related to the id relationships between those tables, for example, both call the *experiments.py* code to get an experiment id. See the Table Schemas for the full set of table interactions. 

The *harvest_metrics.py* and *harvest_innov_stats.py* files handle calls which require harvesting of data via score-hv and then inputs that info into the expt_metrics table via calls to the *expt_metrics.py* code. *harvest_metrics.py* is a more generic version of *harvest_innov_stats.py* and can process any type of harvested data if an appropriate translator is provided in *harvest_translator.py*. Only innov_stats files can be used with *harvest_innov_stats.py*. 

The *harvest_translator.py* file contains the code for translation between score-hv output values and the expected values necessary for inserting into the metrics table. 

The *hv_translator_registry.py* contains the registered translator, found in *harvest_translator.py*, that can be called and is used to process calls appropriately by the specific translator in calls to harvest_metrics. 

The *plot_innov_stats.py* file is used for creating plots about innov stats data. The *innov_stats_plot_attrs.py* file is used for defining attributes used in this plotting.

The **tests** folder contains all the pytests files used for testing. Inside there is a **configs** folder and **experiment-data** folder which contain configurations and data that are necessary for testing purposes and referenced by certain test files. 

Each *test_{name}.py* file is used for testing the code referenced by the name. In general for the database table files it will make a get and a put call in the tests. 

The *.env_example* file is used to show the required inputs for database connections. A *.env* file with the appropriate information, including database password, is required for running. 

The *score_db_utils.sh* bash script is used as a utility for setting up the connection between score-db and score-hv code repositories. It should be run prior to making calls to *score_db_base.py*. The script assumes score-hv is downloaded at the same place as score-db is at a repo level. 

