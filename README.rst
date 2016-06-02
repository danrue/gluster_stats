===============================
Gluster Statistics
===============================

.. image:: https://img.shields.io/pypi/v/gluster_stats.svg
        :target: https://pypi.python.org/pypi/gluster_stats

.. image:: https://img.shields.io/travis/danrue/gluster_stats.svg
        :target: https://travis-ci.org/danrue/gluster_stats


.. image:: https://img.shields.io/badge/license-BSD-blue.svg
        :target: LICENSE

.. image:: https://img.shields.io/badge/python-2.6%20%7C%202.7%20%7C%203.3%20%7C%203.4%20%7C%203.5-green.svg

gluster-stats is a command-line utility that generates health-related gluster
statistics in json, for use in monitoring gluster.

Installation
------------

``pip install gluster-stats``

Usage
-----

Return gluster stats in json format.

``sudo gluster-stats``

Alternatively, use ``gluster-stats --sudo`` to have gluster-stats call all of
the gluster commands with sudo, instead of calling gluster-stats root access
itself.

Example output::

    {
        "brick_stats": {
            "u01gluster": [
                {
                    "disk_free": 824204224102, 
                    "disk_total": 824204224102, 
                    "inode_free": 161060390, 
                    "inode_total": 161060416, 
                    "online": 1
                }, 
                {
                    "disk_free": 824204224102, 
                    "disk_total": 824204224102, 
                    "inode_free": 161060390, 
                    "inode_total": 161060416, 
                    "online": 1
                }, 
                {
                    "disk_free": 824204224102, 
                    "disk_total": 824204224102, 
                    "inode_free": 161060390, 
                    "inode_total": 161060416, 
                    "online": 1
                }
            ]
        }, 
        "generated_timestamp": 1464377824, 
        "gluster_stats_version": "0.0.9", 
        "gluster_version": "3.7.5", 
        "glusterd": 1, 
        "glusterfsd": 1, 
        "peers": 2, 
        "split_brain_entries": {
            "u01gluster": 0
        }, 
        "unhealed_entries": {
            "u01gluster": 0
        }, 
        "volume_count": 1, 
        "volumes": [
            "u01gluster"
        ]
    }

Commands
--------

The following commands are run and parsed to generate the json output:

- ``gluster --version``
- ``gluster peer status``
- ``gluster volume list``
- ``pidof glusterd``
- ``pidof glusterfsd``

For each volume, the following commands are run:

- ``gluster volume heal <volume> info``
- ``gluster volume heal <volume> info split-brain``
- ``gluster volume status <volume> detail``

When run with --sudo, the gluster commands that require sudo access (all but
--version) are run with sudo prepended. 

Testing
-------

Run ``make test``

Tests are run locally with generated mock response files. Run
``gluster-stats-generate`` to generate new mock response file. The file will be
saved at gluster_stats_<gluster_version>.json.

Todo
----

- Use the secret --xml option with ``gluster volume status`` - status was hard
  to parse and the parser is probably fragile. This will require new mock test
  files.
- Additional health checks?
