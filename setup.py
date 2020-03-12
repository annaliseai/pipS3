#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import versioneer
from setuptools import find_packages, setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    'boto3>=1.12.20',
    'Jinja2>=2.11.1',
    'Click>=7.0',
    'versioneer>=0.18',
]

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest>=5.1.2',
    'pytest-cov>=2.7.1',
]

setup(
    author="Ben Johnston",
    author_email='ben.johnston@annalise.ai',
    python_requires='!=2.*, >=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Python Boilerplate contains all the boilerplate you need to create a Python package.",
    entry_points={
        'console_scripts': [
            's3pkgup=s3pkgup.cli:main',
        ],
    },
    install_requires=requirements,
    include_package_data=True,
    keywords='s3pkgup',
    name='s3pkgup',
     package_data={'s3pkgup': ['data/index.html.j2']},
    packages=find_packages(include=['s3pkgup']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://bitbucket.org/harrison-ai/s3pkgup',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    zip_safe=False,
)
