# -*- coding: utf-8 -*-

"""Console script for s3pkgup."""
import sys

import click

from s3pkgup import publish_packages


@click.command()
@click.option('--project', default=None, help='Project Name')
def main(project):
    """Console script for s3pkgup."""
    publish_packages(project)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
