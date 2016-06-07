#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

setup(
    name='gluster-stats',
    version='1.0.0',
    description=('Display gluster stats'),
    long_description=readme + '\n\n' + history,
    author="Dan Rue",
    author_email='drue@therub.org',
    url='https://github.com/danrue/gluster_stats',
    packages=[
        'gluster_stats',
    ],
    package_dir={'gluster_stats':
                 'gluster_stats'},
    include_package_data=True,
    install_requires=['future'],
    license="BSD",
    keywords='gluster monitoring',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=['pytest'],

    entry_points={
        'console_scripts': [
            'gluster-stats=gluster_stats.gluster_stats:main',
            'gluster-stats-generate=gluster_stats.generate_gluster_stats:main',
        ],
    },

)
