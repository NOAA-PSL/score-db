#!/bin/bash --posix

SCORE_DB_HOME_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export PYTHONPATH=$SCORE_DB_HOME_DIR/src
export PYTHONPATH=$SCORE_DB_HOME_DIR/../score-hv/src
echo PYTHONPATH=$PYTHONPATH
echo Python Version: $(python --version)
