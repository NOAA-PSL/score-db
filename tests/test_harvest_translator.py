from collections import namedtuple
from datetime import datetime

from score_db.harvest_translator import daily_bfg_translator

MEDIANTIME = datetime(2025, 1, 1, 12)

# score-hv develop: no segment, region or surface_mask fields
DevelopHarvestedData = namedtuple('HarvestedData', [
    'filenames', 'statistic', 'variable', 'value', 'units', 'mediantime',
    'longname'])

# score-hv daily_bfg with regions and surface masks
HarvestedData = namedtuple('HarvestedData', [
    'filenames', 'segment', 'statistic', 'variable', 'value', 'units',
    'mediantime', 'longname', 'surface_mask', 'region'])


def test_daily_bfg_translator_without_segment_region_or_mask():
    result = daily_bfg_translator(DevelopHarvestedData(
        [], 'mean', 'tmp2m', 280.0, 'K', MEDIANTIME, 'temperature'))

    assert result.name == 'mean_tmp2m'
    assert result.region_name == 'global'
    assert result.usage is None
    assert result.value == 280.0
    assert result.cycletime == MEDIANTIME


def test_daily_bfg_translator_with_segment_region_and_mask():
    result = daily_bfg_translator(HarvestedData(
        [], 'analysis', 'integral', 'icec', 1.0e13, 'm**2', MEDIANTIME,
        'ice concentration', 'water',
        {'name': 'nh', 'latitude': [0, 90], 'longitude': [0, 360]}))

    assert result.name == 'integral_icec_an'
    assert result.region_name == 'nh'
    assert result.usage == 'water'


def test_daily_bfg_translator_background_with_no_mask():
    result = daily_bfg_translator(HarvestedData(
        [], 'background', 'mean', 'tmp2m', 280.0, 'K', MEDIANTIME,
        'temperature', 'none', {'name': 'global'}))

    assert result.name == 'mean_tmp2m_bg'
    assert result.region_name == 'global'
    assert result.usage is None
