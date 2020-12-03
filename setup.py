#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The setup script."""

import versioneer
from setuptools import find_packages, setup

with open('README.md') as readme_file:
    long_description = readme_file.read()

requirements = [
    'boto3>=1.16.4',
    'Click>=7.1.2',
    'versioneer>=0.18',
]

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest>=6.1.1',
    'pytest-cov>=20.10.1',
]

setup(
    author="Ben Johnston",
    author_email='ben.johnston@annalise.ai',
    python_requires='!=2.*, >=3.6',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description=
    "A handy package for creating a simple pypi repo in S3 compliant object storage.",
    entry_points={
        'console_scripts': [
            'pips3=pips3.cli:main',
        ],
    },
    install_requires=requirements,
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords=['pips3', 's3', 'pip', 'pypi'],
    name='pips3',
    packages=find_packages(include=['pips3']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/AnnaliseAI/pipS3',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    zip_safe=False,
)
