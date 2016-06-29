# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from threading import Timer
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree
from builtins import object, str
from __init__ import __version__

class TestCommandNotFound(Exception):
    def __init__(self, value="Test Command Not Found"):
        self.value = value
    def __str__(self):
        return repr(self.value)

class GlusterStats(object):
    """ Collect stats related to gluster from localhost """

    def __init__(self, timeout=None, test_file=False,
                 record_mode=False):
        self.test_commands = []
        if test_file:
            self.test_commands = self._load_test_file(test_file)
        self.timeout = timeout
        self.record_mode=record_mode
        if self.record_mode:
            self.responses = []

        self.gluster_version = self.get_gluster_version()
        self.volumes = self.get_volumes()

    def get_gluster_version(self):
        return self._execute("gluster --version")['stdout'].split()[1]

    def get_volumes(self):
        return self._execute("gluster volume list")['stdout'].strip().split()

    def get_glusterd(self):
        return self._execute("pidof glusterd")['stdout'].strip().split()

    def get_glusterfsd(self):
        return self._execute("pidof glusterfsd")['stdout'].strip().split()

    def get_number_peers(self):
        output = self._execute("gluster peer status")['stdout'].strip()
        return output.count("Peer in Cluster (Connected)")

    def get_unhealed_stats(self):
        stats = {}
        for volume in self.volumes:
            max_entry = 0
            all_entries = self._execute(
                "gluster volume heal {0} info".format(volume))
            if all_entries['timeout_happened']:
                stats[volume] = None
                continue
            for entry in re.findall(r'Number of entries: (\d+)',
                                    all_entries['stdout'], re.MULTILINE):
                max_entry = max(int(entry), max_entry)
            stats[volume] = max_entry
        return stats

    def get_split_brain_stats(self):
        stats = {}
        for volume in self.volumes:
            max_entry = 0
            all_entries = self._execute(
                "gluster volume heal {0} info split-brain".format(
                    volume))
            if all_entries['timeout_happened']:
                stats[volume] = None
                continue
            for entry in re.findall(r'Number of entries in split-brain: (\d+)',
                                    all_entries['stdout'], re.MULTILINE):
                max_entry = max(int(entry), max_entry)
            stats[volume] = max_entry
        return stats

    def _parse_brick_entries_xml(self, all_entries):
        root = ElementTree.fromstring(all_entries)
        bricks = {}
        try:
            root_iterator = root.iter('volume')
        except AttributeError:
            # python 2.6 does not have iter
            root_iterator = root.getiterator('volume')
        for v in root_iterator:
            volName = v.find('volName').text
            nodeCount = v.find('nodeCount').text
            try:
                node_iterator = v.iter('node')
            except AttributeError:
                # python 2.6 does not have iter
                node_iterator = v.getiterator('node')
            for n in node_iterator:
                hostname = n.find('hostname').text
                path = n.find('path').text
                brick = "{0}:{1}".format(hostname, path)
                bricks[brick] = {}
                bricks[brick]['online'] = int(n.find('status').text)
                bricks[brick]['disk_free'] = int(n.find('sizeFree').text)
                bricks[brick]['disk_total'] = int(n.find('sizeTotal').text)

                # Wouldn't this be nice?
                #bricks[brick]['inode_free'] = n.find('inodeFree').text
                #bricks[brick]['inode_total'] = n.find('inodeTotal').text

                bricks[brick]["disk_used"] = (bricks[brick]['disk_total'] -
                                              bricks[brick]['disk_free'])
                bricks[brick]["disk_used_percent"] = format(
                    float(100*bricks[brick]['disk_used'])/
                    float(bricks[brick]['disk_total']), ".2f")

        return bricks

    def _parse_brick_entries(self, all_entries):
        """
        Parses i.e.:
            Brick                : Brick glcom03.p01.ppd:/export/glusterlv/brick1
            TCP Port             : 49152
            RDMA Port            : 0
            Online               : Y
            Pid                  : 3865
            File System          : xfs
            Device               : /dev/mapper/gluster_vg-gluster_lv
            Mount Options        : rw,noatime,nouuid,attr2,inode64,logbsize=256k,sunit=512,swidth=512,noquota
            Inode Size           : 512
            Disk Space Free      : 918.8GB
            Total Disk Space     : 991.5GB
            Inode Count          : 208035840
            Free Inodes          : 206341448
        """
        bricks = {}
        current_brick = ""
        for line in all_entries.split('\n'):
            fields = line.split(' : ')
            if fields[0].strip() == "Brick":
                current_brick = fields[1].split(' ')[-1]
                bricks[current_brick] = {}
            elif fields[0].strip() == "Inode Count":
                bricks[current_brick]['inode_total'] = int(fields[1].strip())
            elif fields[0].strip() == "Free Inodes":
                bricks[current_brick]['inode_free'] = int(fields[1].strip())
            continue

        for brick in bricks:
            bricks[brick]["inode_used"] = bricks[brick]['inode_total'] - bricks[brick]['inode_free']
            bricks[brick]["inode_used_percent"] = format(
                float(100*bricks[brick]['inode_used'])/float(bricks[brick]['inode_total']), ".2f")

        return bricks

    def get_brick_stats(self):
        """
            Call gluster volume status detail twice

            Ideally we only need to call it with --xml. However, --xml does not
            report inode usage (!?). We can't just call without xml, because
            disk space is reported in human readable form, and going from 1.4TB
            to 1.5TB is a 5% jump - far too gross for reporting and trending.
        """
        stats = {}
        for volume in self.volumes:
            all_entries = self._execute(
                "gluster volume status {0} detail".format(volume))
            stat1 = self._parse_brick_entries(all_entries['stdout'])
            all_entries = self._execute(
                "gluster volume status {0} detail --xml".format(volume))
            stat2 = self._parse_brick_entries_xml(all_entries['stdout'])

            # Merge the two dicts
            vol_stats = {}
            for k,v in stat1.items():
                stat = v.copy()
                stat.update(stat2[k])
                vol_stats[k] = stat
            stats[volume] = vol_stats
        return stats

    def get_stats(self):
        self.glusterd = self.get_glusterd()
        self.glusterfsd = self.get_glusterfsd()
        self.peers = self.get_number_peers()
        self.unhealed_entries = self.get_unhealed_stats()
        self.split_brain_entries = self.get_split_brain_stats()
        self.brick_stats = self.get_brick_stats()
        return self._format_stats()

    def _format_stats(self):
        out = {}
        out['volume_count'] = len(self.volumes)
        out['volumes'] = self.volumes
        out['glusterd'] = len(self.glusterd)
        out['glusterfsd'] = len(self.glusterfsd)
        out['peers'] = self.peers
        out['unhealed_entries'] = self.unhealed_entries
        out['split_brain_entries'] = self.split_brain_entries
        out['split_brain_entries'] = self.split_brain_entries
        out['brick_stats'] = self.brick_stats
        out['gluster_version'] = self.gluster_version
        out['gluster_stats_version'] = __version__
        out['generated_timestamp'] = int(time.time())
        return out

    def _load_test_file(self, test_file):
        with open(test_file) as f:
            return json.load(f)

    def _strip_filenames_from_response(self, stdout):
        # Strip file list as they may be private data
        safe_output = []
        for line in stdout.split('\n'):
            if line.startswith("Number"):
                safe_output.append(line)
        return '\n'.join(safe_output)

    def _kill_process_tree(self, process, timeout_happened):
        timeout_happened["value"] = True
        pgid = os.getpgid(process.pid)
        os.killpg(pgid, signal.SIGTERM)

    def _execute(self, cmd):
        if self.test_commands:
            for command in self.test_commands:
                if command['command'] == cmd:
                    return command
            raise TestCommandNotFound(
                "Mock command reponse not found for command '{0}'".format(cmd))

        # Use preexec_fn to create a process group. In case of timeout,
        # the whole process group can be killed.
        p = subprocess.Popen(shlex.split(cmd),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                preexec_fn=os.setpgrp)

        # Create a timer thread to implement timeouts, calling self._kill_process_tree
        # in the event of a timeout to kill the process tree.
        timeout_happened = {"value": False}
        if self.timeout:
            timer = Timer(self.timeout, self._kill_process_tree, [p, timeout_happened])
            timer.start()
        stdout, stderr = p.communicate()
        if self.timeout:
            timer.cancel()

        if p.returncode > 0:
            error = ("ERROR: command '{0}' failed with:\n\n{1}\n\n{2}".
                format(cmd, stdout, stderr))
            print(error, file=sys.stderr)
            sys.exit(p.returncode)
        response = {'command': cmd,
                    'stdout': stdout,
                    'stderr': stderr,
                    'timeout_happened': timeout_happened['value'],
                    'return_code': p.returncode,
                   }

        if self.record_mode:
            if 'heal' in cmd:
                response['stdout'] = self._strip_filenames_from_response(stdout)
            self.responses.append(response)
        return response

    def write_record(self):
        if self.record_mode:
            with open("gluster_stats_{0}_in.json".
                      format(self.gluster_version), 'w') as f:
                f.write(json.dumps(self.responses, indent=4, sort_keys=True))
            with open("gluster_stats_{0}_out.json".
                      format(self.gluster_version), 'w') as f:
                f.write(json.dumps(self._format_stats(), indent=4, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(
        description='Collect stats related to gluster')
    parser.add_argument('--record',
                        help="Record the gluster cli responses in a local response file",
                        action='store_true')
    parser.add_argument('--version',
                        action='version',
                        version='gluster-stats {0}'.format(__version__))
    parser.add_argument('--timeout',
                        default=300,
                        help='Timeout per command in seconds. Defaults to 300.')
    args = parser.parse_args()

    timeout = None
    if args.timeout:
        timeout = int(args.timeout)
    stats = GlusterStats(timeout=timeout,
                         record_mode=args.record)
    print(json.dumps(stats.get_stats(), indent=4, sort_keys=True))
    if args.record:
        stats.write_record()

if __name__ == '__main__':
    main()
