#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Base Class"""

import functools
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
            package_name: Union[str, None] = None,
            continuation_token: Union[str, None] = None) -> Iterable[str]:
        """List keys in S3

        Args:
            max_keys (int, optional): The number of keys to retrieve per attempt. Defaults to 1000.
            package_name (str, optional): List the keys for the specified project only. Defaults to None,
            continuation_token (str, optional): The boto3 continuation token for the next series of responses. Defaults to 1000.

        Yields:
            Iterable[str]: The paths to the keys in the bucket
        """

        kwargs = {
            "Bucket": self.bucket,
            "Prefix": self.prefix
            if package_name is None else f"{self.prefix}/{package_name}",
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

    def generate_index(
        self,
        keys: Union[Iterable[str], None] = None,
        package_name: Union[str, None] = None,
    ) -> str:
        """Generate a pypi index file

        Args:
            keys (Union[Iterable[str], None], optional): The keys of the s3 bucket.
                Defaults to None.  If set to None, a list of S3 keys will be generated.
            package_name (Union[str, None], optional): The package name.  If set to None,
                an index of all packages is generated

        Returns:
            str: The rendered template
        """

        raw_keys = self.list_keys(
            package_name=package_name) if keys is None else keys

        template = INDEX_TEMPLATE_INTO

        for key in raw_keys:
            basename = os.path.basename(key)
            template += f"\n    <a href=\"{self.endpoint}/{key}\">{basename}</a>"

        template += INDEX_TEMPLATE_OUTTRO
        return template

    def upload_package(self,
                       pkg_path: str,
                       package_name: str,
                       public: bool = False,
                       owner_full_control: bool = False):
        """Upload the package to S3

        Args:
            pkg_path (str): The path to the package file to upload
            package_name (str): The name of the package
            public (bool): Set to True to enable Public Read ACL in S3
            owner_full_control (bool, optional): Set to True to provide bucket owner full control.  Defaults to False.
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

            ExtraArgs = {}
            if public:
                ExtraArgs["ACL"] = "public-read"

            if owner_full_control:
                ExtraArgs["ACL"] = "bucket-owner-full-control"

            self.s3_client.upload_file(pkg_path,
                                       self.bucket,
                                       key,
                                       ExtraArgs=ExtraArgs)
            return

        raise PackageExistsException(
            "Package %s already exists in the S3 Bucket for the project %s",
            os.path.basename(pkg_path), package_name)

    def upload_index(self,
                     package_name: Union[str, None] = None,
                     index: Union[str, None] = None,
                     public: bool = False,
                     owner_full_control: bool = False):
        """Upload the index file

        Args:
            package_name (Union[str, None], optional): The name of the package. Defaults to None
            index (Union[str, None], optional): The contents of the index file. Defaults
                to None, where an index file will be automatically generated.
            public (bool, optional): Set to True to enable Public Read ACL in S3.  Defaults to False
            owner_full_control (bool, optional): Set to True to provide bucket owner full control.  Defaults to False.
        """
        generated_index = self.generate_index(
            package_name=package_name) if index is None else index
        key = f'{self.prefix}/{package_name}/index.html'
        logger.info("Uploading index to s3://%s/%s", self.bucket, key)

        put_object = functools.partial(self.s3_client.put_object,
                                       Bucket=self.bucket,
                                       Key=key,
                                       Body=generated_index.encode('utf-8'),
                                       ContentType="text/html")

        if public and not owner_full_control:
            put_object = functools.partial(put_object, ACL='public-read')

        if owner_full_control:
            put_object = functools.partial(put_object, ACL='full-control')

        put_object()


def publish_packages(endpoint: str,
                     bucket: str,
                     public: bool = False,
                     owner_full_control: bool = False):
    """Publish current package files

    Args:
        endpoint (str): The endpoint for the S3-like service
        bucket (str): The name of the bucket to use
        public (bool): Set to True to enable Public Read ACL in S3
        transfer_ownership (bool): Set to True to transfer ownership in S3 to bucket owner
    """

    uploader = PipS3(endpoint, bucket)

    package_name = None

    for upload_file in PipS3.find_package_files():

        # Get the package name
        if package_name is None:

            package_name = os.path.basename(upload_file).split('-')[0]
            package_name = package_name.replace('_', '-')

        uploader.upload_package(upload_file, package_name, public,
                                owner_full_control)

    # Update the index
    uploader.upload_index(package_name)
