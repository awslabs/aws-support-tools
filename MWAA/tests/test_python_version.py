# This Python file uses the following encoding: utf-8
'''
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

"""
Tests that verify_env.py refuses to run on Python 2 instead of carrying on.
"""
import os
import runpy
import sys

import pytest

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'verify_env', 'verify_env.py')


def run_script_as_main():
    sys.path.insert(0, os.path.dirname(SCRIPT))
    try:
        runpy.run_path(SCRIPT, run_name='__main__')
    finally:
        sys.path.remove(os.path.dirname(SCRIPT))


def test_python2_prints_a_message_and_exits_with_an_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'version_info', (2, 7, 18, 'final', 0))
    monkeypatch.setattr(sys, 'argv', ['verify_env.py', '--envname', 'test', '--region', 'us-east-1'])

    with pytest.raises(SystemExit) as exit_info:
        run_script_as_main()

    assert exit_info.value.code == 1
    assert 'python2 detected, please use python3' in capsys.readouterr().out


def test_python3_is_not_stopped_by_the_version_check(monkeypatch, capsys):
    """With Python 3 the script goes on to parse its arguments (and fails on the
    missing --envname), not on the version check."""
    monkeypatch.setattr(sys, 'argv', ['verify_env.py'])

    with pytest.raises(SystemExit) as exit_info:
        run_script_as_main()

    assert exit_info.value.code == 2
    assert 'python2 detected' not in capsys.readouterr().out
