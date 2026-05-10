import os
import boto3
import pytest

def test_aws_env_vars():
    # Check if the pipeline correctly injected the bucket name
    assert "TICKETS_BUCKET" in os.environ
    assert "SQS_URL" in os.environ

def test_s3_client_init():
    # Verify boto3 can initialize without crashing
    s3 = boto3.client('s3', region_name='us-east-1')
    assert s3 is not None