from __future__ import annotations

from functools import lru_cache

import boto3
from botocore.config import Config


_BOTO_CFG = Config(retries={"max_attempts": 3, "mode": "standard"})


@lru_cache(maxsize=1)
def dynamodb_resource():
    return boto3.resource("dynamodb", config=_BOTO_CFG)


def dynamodb_table(name: str):
    return dynamodb_resource().Table(name)


@lru_cache(maxsize=1)
def cognito_idp_client():
    return boto3.client("cognito-idp", config=_BOTO_CFG)