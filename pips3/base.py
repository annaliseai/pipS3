#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Base Class"""

import logging
import os
import sys
from glob import glob
from typing import Iterable, List, Union

import boto3

from pips3.exceptions import PackageExistsException

s3 = boto3.client("s3")

INDEX_TEMPLATE_INTO = "<!DOCTYPE html>\n<html>\n  <body>"
INDEX_TEMPLATE_OUTTRO = "\n  </body>\n</html>"

logging.basicConfig(
    format="%(name)s - %(levelname)s - %(message)s",
    # stream=sys.stdout,
    level=logging.INFO)
logger = logging.getLogger("pips3")


class PipS3:
    """PipS3

    Use S3 compliant object storage as a simple pypi repository

    Args:
        endpoint (str): The storage endpoint e.g. https://some-bucket.s3-website-ap-southeast-2.amazonaws.com 
        bucket (str): The name of the bucket storing the build artifacts
        prefix (str, optional): The prefix to apply to all s3 keys. Defaults to 'simple'
        s3_client (boto3.Session.client, optional): A boto3 S3 session client. Defaults to None, whereby a new
            sesion client will be created using the standard AWS
            [credentials configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html)
    """
    def __init__(
        self,
        endpoint: str,
        bucket: str,
        prefix: str = 'simple',  # The pypi default https://pypi.org/simple
        s3_client: Union[boto3.Session.client, None] = None,
    ):
        self.endpoint = endpoint
        self.bucket = bucket
        self.prefix = prefix

        if s3_client is None:
            s3_client = boto3.client('s3')
        self.s3_client = s3_client

    @staticmethod
    def find_package_files(
        path: str = 'dist',
        pkg_ext: Union[List[str], None] = None,
    ) -> Iterable[str]:
        """Find Python Packages for Upload

        Args:
            path (str, optional): Path to search for packages. Defaults to 'dist'.
            pkg_ext (List[str], optional): Valid file extensions of Python packages to upload.  Defaults to
                None to use standard Python package extensions, .gz and .whl.

        Yields:
            Iterable[str]: The paths to the built packages
        """

        if pkg_ext is None:
            pkg_ext = ['.gz', '.whl']

        search_str = f'{path}/*['
        for ext in pkg_ext:
            search_str += f'({ext})||'
        search_str = search_str[:-2] + ']'

        for pref in glob(search_str):
            yield pref

    def list_keys(
            self,
            max_keys: int = 1000,
            project_name: Union[str, None] = None,
            continuation_token: Union[str, None] = None) -> Iterable[str]:
        """List keys in S3

        Args:
            max_keys (int, optional): The number of keys to retrieve per attempt. Defaults to 1000.
            project_name (str, optional): List the keys for the specified project only. Defaults to None,
            continuation_token (str, optional): The boto3 continuation token for the next series of responses. Defaults to 1000.

        Yields: 
            Iterable[str]: The paths to the keys in the bucket
        """

        kwargs = {
            "Bucket": self.bucket,
            "Prefix": self.prefix
            if project_name is None else f"{self.prefix}/{project_name}",
            "MaxKeys": max_keys,
        }
        if continuation_token is not None:
            kwargs['ContinuationToken'] = continuation_token

        logger.info("Listing objects in s3://%s/%s", self.bucket, self.prefix)
        response = self.s3_client.list_objects_v2(**kwargs)

        for key in response['Contents']:
            yield key["Key"]

        if 'NextContinuationToken' in response:
            for key in self.list_keys(
                    max_keys=max_keys,
                    continuation_token=response['NextContinuationToken']):
                yield key

    def generate_index(self, keys: Union[Iterable[str], None] = None) -> str:
        """Generate a pypi index file

        Args:
            keys (Union[Iterable[str], None], optional): The keys of the s3 bucket.
                Defaults to None.  If set to None, a list of S3 keys will be generated.

        Returns:
            str: The rendered template
        """

        raw_keys = self.list_keys() if keys is None else keys

        template = INDEX_TEMPLATE_INTO

        for key in raw_keys:
            basename = os.path.basename(key)
            template += f"\n    <a href=\"{self.endpoint}/{key}\">{basename}</a>"

        template += INDEX_TEMPLATE_OUTTRO
        return template

    def upload_package(self, pkg_path: str, package_name: str):
        """Upload the package to S3

        Args:
            pkg_path (str): The path to the package file to upload 
            package_name (str): The name of the package 

        Raises:
            PackageExistsException: If a package file with the same name
                already exists for this project
        """

        key = os.path.join(self.prefix, package_name,
                           os.path.basename(pkg_path))
        logger.info("Uploading %s to s3://%s/%s", pkg_path, self.bucket, key)

        # If the file already exists, do not override
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)

        # The files does not exist we can upload
        except self.s3_client.exceptions.ClientError:
            self.s3_client.upload_file(pkg_path,
                                       self.bucket,
                                       key,
                                       ExtraArgs={"ACL": "public-read"})
            return

        raise PackageExistsException(
            "Package %s already exists in the S3 Bucket for the project %s",
            os.path.basename(pkg_path), package_name)

    def upload_index(self, package_name: str, index: Union[str, None] = None):
        """Upload the index file

        Args:
            package_name (str): The name of the package 
            index (Union[str, None], optional): The contents of the index file. Defaults
                to None, where an index file will be automatically generated.
        """
        generated_index = self.generate_index() if index is None else index
        key = f'{self.prefix}/{package_name}/index.html'
        logger.info("Uploading index to s3://%s/%s", self.bucket, key)
        self.s3_client.put_object(Bucket=self.bucket,
                                  Key=key,
                                  Body=generated_index.encode('utf-8'),
                                  ACL="public-read",
                                  ContentType="text/html")


def publish_packages(endpoint: str, bucket: str, package_name: str):
    """Publish current package files

    Args:
        endpoint (str): The endpoint for the S3-like service 
        bucket (str): The name of the bucket to use 
        package_name (str): The name of the package 
    """

    uploader = PipS3(endpoint, bucket)

    for upload_file in PipS3.find_package_files():
        uploader.upload_package(upload_file, package_name)

    # Update the index
    uploader.upload_index(package_name)
