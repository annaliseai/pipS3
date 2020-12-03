#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exceptions"""


class PackageExistsException(Exception):
    """Package already exists"""


class InvalidConfig(Exception):
    """Invalid configuration"""