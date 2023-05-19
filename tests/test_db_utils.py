"""
Copyright 2022 NOAA
All rights reserved.

Unit tests for db_utils

"""
import os
import pathlib
import pytest
import json
from collections import namedtuple

import db_utils

PYTEST_CALLING_DIR = pathlib.Path(__file__).parent.resolve()

def test_validate_method():
    with pytest.raises(ValueError):
        db_utils.validate_method('blah')
    
    with pytest.raises(ValueError):
        db_utils.validate_method(None)
    
    with pytest.raises(ValueError):
        db_utils.validate_method([])
    
    for method in db_utils.VALID_METHODS:
        db_utils.validate_method(method)
    
    print(f'PYTEST_CALLING_DIR: {PYTEST_CALLING_DIR}')
