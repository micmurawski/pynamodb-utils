import json

import boto3
from moto import mock_dynamodb, mock_iam, mock_sts
from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model




def test_as_remote_table():
    with mock_dynamodb(), mock_iam(), mock_sts():
        from pynamodb_utils.decorators import as_remote_table
        iam_client = boto3.client('iam', region_name='us-east-1')
        assume_role_policy_document = json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "123456789012"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        })
        iam_response = iam_client.create_role(
            RoleName='table-access-role',
            AssumeRolePolicyDocument=assume_role_policy_document
        )
        iam_client.attach_role_policy(
            PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess',
            RoleName='table-access-role'
        )
        print(iam_response['Role']['Arn'])

        @as_remote_table(role_arn=iam_response['Role']['Arn'], table_name='example-table-name', region='us-east-1')
        class Article(Model):
            source_trust_domain_id = UnicodeAttribute(hash_key=True)
            trusted_domain_id = UnicodeAttribute(range_key=True)

        print(Article.Meta.table_name)
        print(Article.Meta.region)
        Article.create_table()
