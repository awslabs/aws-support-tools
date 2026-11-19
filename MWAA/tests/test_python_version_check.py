'''
Unit test for the Python 2 check at the top of verify_env.py.

The check has to run before verify_env.py imports the verifier modules, whose
f-strings Python 2 cannot parse. This test fakes a Python 2 version and checks
that the script exits with status 1 before importing them.

Run from the MWAA folder:  python -m pytest tests/test_python_version_check.py
'''
import os
import runpy
import sys

import pytest

VERIFY_ENV_DIR = os.path.join(os.path.dirname(__file__), '..', 'verify_env')


def test_python2_exits_before_importing_the_verifiers(monkeypatch, capsys):
    monkeypatch.syspath_prepend(VERIFY_ENV_DIR)
    monkeypatch.delitem(sys.modules, 'cloudwatch_verifier', raising=False)
    monkeypatch.setattr(sys, 'version_info', (2, 7, 18, 'final', 0))

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(os.path.join(VERIFY_ENV_DIR, 'verify_env.py'), run_name='__main__')

    assert exc_info.value.code == 1
    assert 'python3' in capsys.readouterr().out
    assert 'cloudwatch_verifier' not in sys.modules
