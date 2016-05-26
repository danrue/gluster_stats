===============================
Gluster Statistics
===============================

.. image:: https://img.shields.io/pypi/v/gluster_stats.svg
        :target: https://pypi.python.org/pypi/gluster_stats

.. image:: https://img.shields.io/travis/danrue/gluster_stats.svg
        :target: https://travis-ci.org/danrue/gluster_stats

gluster-stats is a command-line utility that generates health-related gluster
statistics in json, for use in monitoring gluster.

Installation
------------

``pip install gluster-stats``

Usage
-----

Return gluster stats in json format.

``sudo gluster-stats``

Example output::

    {
        "brick_stats": {
            "u01gluster": [
                {
                    "disk_free": 824204224102, 
                    "disk_total": 824204224102, 
                    "inode_free": "161060390", 
                    "inode_total": "161060416", 
                    "online": 1
                }, 
                {
                    "disk_free": 824204224102, 
                    "disk_total": 824204224102, 
                    "inode_free": "161060390", 
                    "inode_total": "161060416", 
                    "online": 1
                }, 
                {
                    "disk_free": 824204224102, 
                    "disk_total": 824204224102, 
                    "inode_free": "161060390", 
                    "inode_total": "161060416", 
                    "online": 1
                }
            ]
        }, 
        "glusterd": 1, 
        "glusterfsd": 1, 
        "peers": 2, 
        "split_brain_entries": {
            "u01gluster": 0
        }, 
        "unhealed_entries": {
            "u01gluster": 0
        }, 
        "volumes": 1
    }

Generate mock test response file in gluster_stats_<gluster_version>.json.

``gluster-stats-generate``
