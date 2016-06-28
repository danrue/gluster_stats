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

    def test_375_default(self):
        """ Normal Run """
        stats = gluster_stats.GlusterStats(
                  test_file="tests/test_sources/gluster_stats_3.7.5_in.json")
        output = stats.get_stats()
        del output['generated_timestamp'] # Remove dynamic keys
        del output['gluster_stats_version'] # Remove dynamic keys

        #print(json.dumps(output, indent=1, sort_keys=True))

        with open('tests/test_sources/gluster_stats_3.7.5_out.json') as f:    
            expected_out = json.load(f)
        del expected_out['generated_timestamp'] # Remove dynamic keys
        del expected_out['gluster_stats_version'] # Remove dynamic keys

        assert output == expected_out
