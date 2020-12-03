# -*- coding: utf-8 -*-
"""Console script for pips3."""
import os
import sys

import click

from pips3 import publish_packages
from pips3.exceptions import InvalidConfig


@click.command()
@click.option('--endpoint', default=None, help='S3 Endpoint')
@click.option('--bucket', default=None, help='S3 Bucket')
def main(endpoint, bucket):
    """Console script for pips3."""

    # Try a number of options for determining configuration values
    endpoint = os.getenv('PIPS3_ENDPOINT') if endpoint is None else endpoint
    bucket = os.getenv('PIPS3_BUCKET') if bucket is None else bucket

    # TODO: #2 Allow retrieving of values from pip.conf

    # If the values are still not specified raise errors
    if endpoint is None:
        raise InvalidConfig("Error!!! S3 endpoint not specified")

    if bucket is None:
        raise InvalidConfig("Error!!! S3 bucket not specified")

    publish_packages(endpoint, bucket)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
