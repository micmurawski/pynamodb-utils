import os
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from pynamodb.settings import default_settings_dict


def as_remote_table(role_arn, session_name=uuid4().hex, **kwargs):
    def decorator(klass):
        _region = kwargs.get('region') or os.environ.get('AWS_REGION', 'us-east-1')
        sts_client = boto3.client('sts', endpoint_url=f"https://sts.{_region}.amazonaws.com", region_name=_region)
        sts_response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name
        )

        class NewKlass(klass):
            class Meta:
                table_name = kwargs.get('table_name')
                aws_access_key_id = sts_response["Credentials"]["AccessKeyId"]
                aws_secret_access_key = sts_response["Credentials"]["SecretAccessKey"]
                aws_session_token = sts_response["Credentials"]["SessionToken"]
                region = _region
                host = kwargs.get('host')
                connect_timeout_seconds = default_settings_dict['connect_timeout_seconds']
                read_timeout_seconds = default_settings_dict['read_timeout_seconds']
                max_retry_attempts = default_settings_dict['max_retry_attempts']
                base_backoff_ms = default_settings_dict['base_backoff_ms']
                max_pool_connections = default_settings_dict['max_pool_connections']
                extra_headers = default_settings_dict['extra_headers']

        NewKlass.__name__ = klass.__name__
        NewKlass.__doc__ = klass.__doc__
        
        return NewKlass

    return decorator
