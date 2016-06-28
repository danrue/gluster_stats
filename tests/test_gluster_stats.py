#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_gluster_stats
----------------------------------

Tests for `gluster_stats` module.
"""
import glob
import hashlib
import json
import os
import shutil
from gluster_stats import gluster_stats
from builtins import object


class TestGlusterStats(object):
    """ Test gluster-stats """

    def test_default(self):
        """ Normal Run """

        ins = glob.glob("tests/test_sources/gluster_stats*_in.json")
        outs = glob.glob("tests/test_sources/gluster_stats*_out.json")
        for in_file in ins:
            out_file = in_file.replace("_in.json", "_out.json")
            assert out_file in outs

            print("Testing {0}".format(in_file))

            stats = gluster_stats.GlusterStats(test_file=in_file)
            output = stats.get_stats()
            del output['generated_timestamp'] # Remove dynamic keys
            del output['gluster_stats_version'] # Remove dynamic keys

            #print(json.dumps(output, indent=1, sort_keys=True))

            with open(out_file) as f:
                expected_out = json.load(f)
            del expected_out['generated_timestamp'] # Remove dynamic keys
            del expected_out['gluster_stats_version'] # Remove dynamic keys

            assert output == expected_out
