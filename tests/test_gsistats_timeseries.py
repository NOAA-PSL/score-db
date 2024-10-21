import score_db.gsistats_timeseries as gsiplot
import pytest

def test_run_plot():
    gsiplot.run()

def test_line_plot_multi():
    gsiplot.run_line_plot()