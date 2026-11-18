'''
Unit tests for assign_private_ip_v2.py.

The script shells out for everything, so subprocess is replaced with fakes.
Like the real check_output, the fake returns bytes unless universal_newlines
(or text) is set. No EMR node, AWS account or sudo is needed.

Run from this folder:  python -m pytest test_assign_private_ip_v2.py
'''
import os
import runpy
import subprocess
import sys

import pytest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assign_private_ip_v2.py')

OUTPUTS = {
    'instance.json': 'true\n',
    'meta-data/instance-id': 'i-0abc1234',
    'NetworkInterfaceId': '"eni-0abc1234"\n',
    'SubnetId': '"subnet-0abc1234"\n',
    'describe-subnets': '"172.31.32.0/20"\n',
    'meta-data/local-ipv4': '172.31.40.10\n',
}


@pytest.fixture
def fake_shell(monkeypatch):
    calls = []

    def check_output(cmd, **kwargs):
        for key, out in OUTPUTS.items():
            if key in cmd[0]:
                if kwargs.get('universal_newlines') or kwargs.get('text'):
                    return out
                return out.encode()
        raise AssertionError('unexpected command: %s' % cmd[0])

    def check_call(cmd, **kwargs):
        calls.append(cmd[0])
        return 0

    monkeypatch.setattr(subprocess, 'check_output', check_output)
    monkeypatch.setattr(subprocess, 'check_call', check_call)
    monkeypatch.setattr(sys, 'argv', [SCRIPT, '172.31.45.7', 'us-east-1'])
    return calls


def test_shebang_uses_python3():
    with open(SCRIPT) as f:
        assert f.readline().strip() == '#!/usr/bin/python3'


def test_master_node_assigns_ip(fake_shell):
    runpy.run_path(SCRIPT, run_name='__main__')
    assert fake_shell == [
        'aws ec2 assign-private-ip-addresses --region us-east-1 '
        '--network-interface-id eni-0abc1234 --private-ip-addresses 172.31.45.7',
        'sudo ip addr add dev eth0 172.31.45.7/20',
        'sudo iptables -t nat -A PREROUTING -d 172.31.45.7 -j DNAT --to-destination 172.31.40.10',
    ]


def test_non_master_node_does_nothing(fake_shell, monkeypatch, capsys):
    monkeypatch.setitem(OUTPUTS, 'instance.json', 'false\n')
    runpy.run_path(SCRIPT, run_name='__main__')
    assert fake_shell == []
    assert capsys.readouterr().out.strip() == 'Not the master node'
