#!/bin/bash --posix

SCORE_DB_HOME_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo Python binary: $(which python)
echo PYTHONPATH=$PYTHONPATH
echo Python version: $(python --version)
