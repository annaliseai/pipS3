# -*- coding: utf-8 -*-
"""Top-level package for pips3."""

__author__ = """Ben Johnston"""
__email__ = 'ben.johnston@annalise.ai'

from ._version import get_versions

__version__ = get_versions()['version']
del get_versions

from pips3.base import PipS3, publish_packages
