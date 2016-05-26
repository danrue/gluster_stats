#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_gluster_stats
----------------------------------

Tests for `gluster_stats` module.
"""
import hashlib
import json
import os
import shutil
from gluster_stats import gluster_stats
from builtins import object


class TestGlusterStats(object):
    """ Test gluster-stats """

    def test_378_default(self):
        """ Normal Run """
        stats = gluster_stats.GlusterStats(
                  test_file="tests/test_sources/gluster_stats_3.7.8.json")
        output = stats.get_stats()
        #print(json.dumps(output, indent=1, sort_keys=True))
        assert output == {
             "brick_stats": {
              "preprodcomms": [
               {
                "disk_free": 982151646412, 
                "disk_total": 1064615018496, 
                "inode_free": "206325202", 
                "inode_total": "208035840", 
                "online": 1
               }, 
               {
                "disk_free": 984191755878, 
                "disk_total": 1064615018496, 
                "inode_free": "206325528", 
                "inode_total": "208035840", 
                "online": 1
               }, 
               {
                "disk_free": 985802368614, 
                "disk_total": 1064615018496, 
                "inode_free": "206325083", 
                "inode_total": "208035840", 
                "online": 1
               }
              ]
             }, 
             "glusterd": 1, 
             "glusterfsd": 1, 
             "peers": 2, 
             "split_brain_entries": {
              "preprodcomms": 0
             }, 
             "unhealed_entries": {
              "preprodcomms": 855
             }, 
             "volumes": 1
            }

    def test_375_default(self):
        """ Normal Run """
        stats = gluster_stats.GlusterStats(
                  test_file="tests/test_sources/gluster_stats_3.7.5.json")
        output = stats.get_stats()
        #print(json.dumps(output, indent=1, sort_keys=True))
        assert output == {
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
