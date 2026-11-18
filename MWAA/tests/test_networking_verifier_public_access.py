import pytest
from botocore.exceptions import ClientError

from verify_env.networking_verifier import NetworkingVerifier

ALL_BLOCKED = {
    'BlockPublicAcls': True,
    'IgnorePublicAcls': True,
    'BlockPublicPolicy': True,
    'RestrictPublicBuckets': True,
}

ONLY_BLOCK_PUBLIC_ACLS = {
    'BlockPublicAcls': True,
    'IgnorePublicAcls': False,
    'BlockPublicPolicy': False,
    'RestrictPublicBuckets': False,
}


class FakeReport:
    def __init__(self):
        self.messages = []

    def write_all_locations(self, *args, sep=' ', end='\n\n'):
        self.messages.append(sep.join(str(arg) for arg in args))


class FakeS3Client:
    def __init__(self, config):
        self.config = config

    def get_public_access_block(self, **kwargs):
        if self.config is None:
            raise ClientError(
                {
                    'Error': {
                        'Code': 'NoSuchPublicAccessBlockConfiguration',
                        'Message': 'The public access block configuration was not found',
                    }
                },
                'GetPublicAccessBlock',
            )
        return {'PublicAccessBlockConfiguration': self.config}


def make_verifier():
    verifier = object.__new__(NetworkingVerifier)
    verifier.report = FakeReport()
    return verifier


@pytest.mark.parametrize(
    'config,expected',
    [
        (ALL_BLOCKED, True),
        (ONLY_BLOCK_PUBLIC_ACLS, False),
        (None, False),
    ],
)
def test_check_access_blocked_requires_all_four_settings(config, expected):
    verifier = make_verifier()

    actual = verifier._check_access_blocked(
        'bucket', FakeS3Client(config), Bucket='example-bucket'
    )

    assert actual is expected


def test_partial_bucket_config_does_not_count_as_blocked():
    verifier = make_verifier()
    verifier.env = {
        'SourceBucketArn': 'arn:aws:s3:::example-bucket',
        'Arn': 'arn:aws:airflow:us-east-1:123456789012:environment/example',
    }
    verifier.s3 = FakeS3Client(ONLY_BLOCK_PUBLIC_ACLS)
    verifier.s3control = FakeS3Client(None)

    verifier.check_s3_block_public_access()

    assert any('does NOT block public access' in message
               for message in verifier.report.messages)


def test_all_four_settings_on_bucket_still_count_as_blocked():
    verifier = make_verifier()
    verifier.env = {
        'SourceBucketArn': 'arn:aws:s3:::example-bucket',
        'Arn': 'arn:aws:airflow:us-east-1:123456789012:environment/example',
    }
    verifier.s3 = FakeS3Client(ALL_BLOCKED)
    verifier.s3control = FakeS3Client(None)

    verifier.check_s3_block_public_access()

    assert any('✅ s3 bucket' in message for message in verifier.report.messages)
