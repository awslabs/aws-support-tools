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
Tests for AWSClients credential handling.
Validates that the --profile argument is optional and that
boto3's default credential chain is used when no profile is specified.
"""
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'verify_env'))

from aws_clients import AWSClients


class TestAWSClientsProfile:
    """Tests for profile handling in AWSClients."""

    @patch('aws_clients.boto3.client')
    @patch('aws_clients.boto3.setup_default_session')
    def test_no_profile_skips_session_setup(self, mock_setup_session, mock_client):
        """When profile is None, setup_default_session should not be called."""
        mock_client.return_value = MagicMock()
        AWSClients(region='us-east-1', profile=None)
        mock_setup_session.assert_not_called()

    @patch('aws_clients.boto3.client')
    @patch('aws_clients.boto3.setup_default_session')
    def test_no_profile_default_arg(self, mock_setup_session, mock_client):
        """When profile is omitted entirely, setup_default_session should not be called."""
        mock_client.return_value = MagicMock()
        AWSClients(region='us-east-1')
        mock_setup_session.assert_not_called()

    @patch('aws_clients.boto3.client')
    @patch('aws_clients.boto3.setup_default_session')
    def test_explicit_profile_sets_session(self, mock_setup_session, mock_client):
        """When a profile is explicitly provided, setup_default_session is called with it."""
        mock_client.return_value = MagicMock()
        AWSClients(region='us-east-1', profile='myprofile')
        mock_setup_session.assert_called_once_with(profile_name='myprofile')

    @patch('aws_clients.boto3.client')
    @patch('aws_clients.boto3.setup_default_session')
    def test_all_clients_created(self, mock_setup_session, mock_client):
        """All expected boto3 clients are created regardless of profile setting."""
        mock_client.return_value = MagicMock()
        AWSClients(region='eu-west-1', profile=None)
        expected_services = ['ec2', 's3', 's3control', 'logs', 'kms',
                           'cloudtrail', 'ssm', 'iam', 'mwaa', 'cloudwatch']
        assert mock_client.call_count == len(expected_services)
        # Verify each service was requested with the correct region
        for call in mock_client.call_args_list:
            assert call[1]['region_name'] == 'eu-west-1'
