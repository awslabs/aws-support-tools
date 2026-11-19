'''
Unit tests for utils.str2bool.

Run from the DRS-Settings-Tool folder:  python -m pytest test_str2bool.py
'''
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from utils.str2bool import str2bool  # noqa: E402


@pytest.mark.parametrize('value', ['true', 'True', 'TRUE', ' true '])
def test_true_values(value):
    assert str2bool(value) is True


@pytest.mark.parametrize('value', ['false', 'False', 'FALSE', ' false '])
def test_false_values(value):
    assert str2bool(value) is False


@pytest.mark.parametrize('value', ['', 't', 'rue', 'alse', 'yes'])
def test_other_values_are_not_treated_as_booleans(value):
    # An empty CSV cell used to be read as True because of a substring match
    assert str2bool(value) is None
