#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `pips3` package."""

from unittest.mock import MagicMock, call, patch

import boto3
import pytest
from moto import mock_s3

from pips3 import PipS3, publish_packages
from pips3.exceptions import PackageExistsException

ENDPOINT_URL = "http://localhost:9000"
BUCKET = 'pips3'
PREFIX = 'listing'


@mock_s3
def test_list_bucket():
    """Test listing bucket"""

    s3_client = boto3.client('s3', region_name='us-east-1')

    ## Populate the bucket with some files
    s3_client.create_bucket(Bucket=BUCKET)

    expected_keys = []

    for i in range(11):

        key = f'{PREFIX}/{i}.bin'
        s3_client.put_object(
            Bucket=BUCKET,
            Body=f'{i}'.encode(),
            Key=key,
        )
        expected_keys.append(key)

    # Create PipS3 object
    obj = PipS3(ENDPOINT_URL, BUCKET, PREFIX, s3_client)

    keys = [key for key in obj.list_keys(max_keys=2)]

    expected_keys.sort()
    keys.sort()

    assert keys == expected_keys


def test_find_packages():
    """Test finding packages"""

    packages = [
        pkg for pkg in PipS3.find_package_files(path='docs',
                                                pkg_ext=['.rst', '.bat'])
    ]

    expected = [
        'docs/index.rst', 'docs/installation.rst', 'docs/readme.rst',
        'docs/usage.rst', 'docs/make.bat'
    ]

    packages.sort()
    expected.sort()

    assert packages == expected


def test_generate_index_template():
    """Test generating index template"""

    obj = PipS3(ENDPOINT_URL, BUCKET, PREFIX)
    some_keys = [f'{PREFIX}/foo.whl', f'{PREFIX}/bar.whl']

    expected_template = f"""<!DOCTYPE html>
<html>
  <body>
    <a href="{ ENDPOINT_URL }/{PREFIX}/foo.whl">foo.whl</a>
    <a href="{ ENDPOINT_URL }/{PREFIX}/bar.whl">bar.whl</a>
  </body>
</html>"""

    assert obj.generate_index(keys=some_keys) == expected_template


@mock_s3
def test_upload_package():
    """Test uploading a package to the correct project"""

    s3_client = boto3.client('s3', region_name='us-east-1')
    s3_client.create_bucket(Bucket=BUCKET)

    fake_pkg = 'README.md'

    obj = PipS3(ENDPOINT_URL, BUCKET, PREFIX)

    project_name = "pips3"

    obj.upload_package(fake_pkg, project_name)

    # Check the file exists at the expected path
    s3_client.head_object(Bucket=BUCKET,
                          Key=f'{PREFIX}/{project_name}/{fake_pkg}')

    # Test error when trying to upload twice
    with pytest.raises(PackageExistsException):
        obj.upload_package(fake_pkg, project_name)


@mock_s3
def test_upload_index():
    """Test uploading an index"""

    s3_client = boto3.client('s3', region_name='us-east-1')
    s3_client.create_bucket(Bucket=BUCKET)

    obj = PipS3(ENDPOINT_URL, BUCKET, PREFIX)

    project_name = "pips3"
    index = "index.html"

    obj.upload_index(project_name, index, False)

    # Check the file exists at the expected path
    s3_client.head_object(Bucket=BUCKET,
                          Key=f'{PREFIX}/{project_name}/index.html')


@mock_s3
@patch('pips3.base.PipS3.find_package_files',
       return_value=[
           'tests/assets/pips3-0.1.0.dev0.whl',
           'tests/assets/pips3-0.1.0.whl',
       ])
def test_publish_packages(files_mock):
    """Publish packages"""

    s3_client = boto3.client('s3', region_name='us-east-1')
    s3_client.create_bucket(Bucket=BUCKET)

    prefix = "simple"

    publish_packages(ENDPOINT_URL, BUCKET, False)

    # Get the index
    index = s3_client.get_object(Bucket=BUCKET,
                                 Key=f'{prefix}/pips3/index.html')
    index = index['Body'].read().decode('utf-8')

    expected_index = f"""<!DOCTYPE html>
<html>
  <body>
    <a href="{ ENDPOINT_URL }/simple/pips3/pips3-0.1.0.dev0.whl">pips3-0.1.0.dev0.whl</a>
    <a href="{ ENDPOINT_URL }/simple/pips3/pips3-0.1.0.whl">pips3-0.1.0.whl</a>
  </body>
</html>"""

    assert index == expected_index


@mock_s3
@patch('pips3.base.PipS3.find_package_files',
       return_value=[
           'tests/assets/pips3-0.1.0.dev0.whl',
           'tests/assets/pips3-0.1.0.whl',
       ])
def test_upload_index_public(files_mock):
    """Upload packages with public ACL"""

    uploader = PipS3('http://endpoint', 'some-bucket', s3_client=MagicMock())
    uploader.upload_index('tests/assets/pips3-0.1.0.whl', 'some-pkg', True)

    assert call(Bucket='some-bucket',
                Key='simple/tests/assets/pips3-0.1.0.whl/index.html',
                Body=b'some-pkg',
                ACL='public-read',
                ContentType='text/html'
                ) in uploader.s3_client.put_object.call_args_list
