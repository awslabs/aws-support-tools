# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://aws.amazon.com/apache2.0/
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import gzip
import importlib.util
import io
import sys
import types
from pathlib import Path


def test_lambda_handler_sends_email_with_python3(monkeypatch):
    sent_messages = []
    requested_keys = []

    class Body:
        def __init__(self, value):
            self.value = io.BytesIO(value)

        def read(self):
            return self.value.read()

    class S3Client:
        def get_object(self, Bucket, Key):
            requested_keys.append(Key)
            if Key == "uploads/customer list.csv.gz":
                csv_data = (
                    "sender@example.com,recipient@example.com,Welcome,Hello there!\n"
                ).encode("utf-8")
                return {"Body": Body(gzip.compress(csv_data))}
            if Key == "text.txt":
                return {"Body": Body(b"Hello from the template")}
            raise FileNotFoundError(Key)

        def delete_object(self, Bucket, Key):
            return {"ResponseMetadata": {"HTTPStatusCode": 204}}

    class SESClient:
        def send_raw_email(self, **kwargs):
            sent_messages.append(kwargs)
            return {"MessageId": "test-message"}

    clients = {"s3": S3Client(), "ses": SESClient()}
    boto3 = types.ModuleType("boto3")
    boto3.client = lambda service, region_name: clients[service]
    botocore = types.ModuleType("botocore")
    botocore.exceptions = types.SimpleNamespace(ClientError=Exception)

    monkeypatch.setenv("REGION", "us-east-1")
    monkeypatch.setenv("MAX_THREADS", "2")
    monkeypatch.setenv("TEXT_MESSAGE_FILE", "text.txt")
    monkeypatch.setenv("HTML_MESSAGE_FILE", "missing.html")
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    monkeypatch.setitem(sys.modules, "botocore", botocore)

    module_path = Path(__file__).with_name("ses_mailer.py")
    spec = importlib.util.spec_from_file_location("ses_mailer_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "mail-bucket"},
                    "object": {"key": "uploads/customer+list.csv.gz"},
                }
            }
        ]
    }
    module.lambda_handler(event, None)

    assert requested_keys == [
        "uploads/customer list.csv.gz",
        "text.txt",
        "missing.html",
    ]
    assert len(sent_messages) == 1
    assert sent_messages[0]["Source"] == "sender@example.com"
    assert sent_messages[0]["Destinations"] == ["recipient@example.com"]
    assert "Hello from the template" in sent_messages[0]["RawMessage"]["Data"]
