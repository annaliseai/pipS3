# -*- coding: utf-8 -*-

"""Console script for s3pkgup."""
import sys

import click

from s3pkgup import publish_wheel


@click.command()
def main(args=None):
    """Console script for s3pkgup."""
    publish_wheel()
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
