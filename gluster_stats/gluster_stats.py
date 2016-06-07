from __future__ import print_function
import argparse
import json
import re
import subprocess
import sys
import time

from builtins import object, str
from __init__ import __version__

class TestCommandNotFound(Exception):
    def __init__(self, value="Test Command Not Found"):
        self.value = value
    def __str__(self):
        return repr(self.value)

class GlusterStats(object):
    """ Collect stats related to gluster from localhost """

    def __init__(self, use_sudo=False, test_file=False):
        self.test_commands = []
        if test_file:
            self.test_commands = self._load_test_file(test_file)
        self.use_sudo = use_sudo

        self.gluster_version = self.get_gluster_version()
        self.volumes = self.get_volumes()

    def get_gluster_version(self):
        return self._execute("gluster --version").split()[1]

    def get_volumes(self):
        return self._execute("gluster volume list", req_sudo=True).strip().split()

    def get_glusterd(self):
        return self._execute("pidof glusterd").strip().split()

    def get_glusterfsd(self):
        return self._execute("pidof glusterfsd").strip().split()

    def get_number_peers(self):
        output = self._execute("gluster peer status", req_sudo=True).strip()
        return output.count("Peer in Cluster (Connected)")

    def get_unhealed_stats(self):
        stats = {}
        for volume in self.volumes:
            entries = 0
            all_entries = self._execute(
                "gluster volume heal {0} info".format(volume), req_sudo=True)
            for entry in re.findall(r'Number of entries: (\d+)',
                                    all_entries, re.MULTILINE):
                entries += int(entry)
            stats[volume] = entries
        return stats

    def get_split_brain_stats(self):
        stats = {}
        for volume in self.volumes:
            entries = 0
            all_entries = self._execute(
                "gluster volume heal {0} info split-brain".format(
                    volume), req_sudo=True)
            for entry in re.findall(r'Number of entries in split-brain: (\d+)',
                                    all_entries, re.MULTILINE):
                entries += int(entry)
            stats[volume] = entries
        return stats

    def _dehumanize_size(self, byte_string):
        """ Convert strings such as '918.8GB' to bytes. """
        if "TB" in byte_string:
            return int(float(byte_string[:-2])*2**40)
        elif "GB" in byte_string:
            return int(float(byte_string[:-2])*2**30)
        elif "MB" in byte_string:
            return int(float(byte_string[:-2])*2**20)
        elif "KB" in byte_string:
            return int(float(byte_string[:-2])*2**10)

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

            elif fields[0].strip() == "Online":
                online = fields[1].strip()
                if online == 'Y':
                    bricks[current_brick]['online'] = 1
                else:
                    bricks[current_brick]['online'] = 0
            elif fields[0].strip() == "Disk Space Free":
                bricks[current_brick]['disk_free'] = self._dehumanize_size(
                    fields[1].strip())
            elif fields[0].strip() == "Total Disk Space":
                bricks[current_brick]['disk_total'] = self._dehumanize_size(
                    fields[1].strip())
            elif fields[0].strip() == "Inode Count":
                bricks[current_brick]['inode_total'] = int(fields[1].strip())
            elif fields[0].strip() == "Free Inodes":
                bricks[current_brick]['inode_free'] = int(fields[1].strip())
            continue

        for brick in bricks:
            bricks[brick]["disk_used"] = bricks[brick]['disk_total'] - bricks[brick]['disk_free']
            bricks[brick]["disk_used_percent"] = format(
                float(bricks[brick]['disk_used'])/float(bricks[brick]['disk_total']), ".2f")
            bricks[brick]["inode_used"] = bricks[brick]['inode_total'] - bricks[brick]['inode_free']
            bricks[brick]["inode_used_percent"] = format(
                float(bricks[brick]['inode_used'])/float(bricks[brick]['inode_total']), ".2f")

        return bricks

    def get_brick_stats(self):
        stats = {}
        for volume in self.volumes:
            all_entries = self._execute(
                "gluster volume status {0} detail".format(
                    volume), req_sudo=True)
            stats[volume] = self._parse_brick_entries(all_entries)
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

    def _execute(self, cmd, req_sudo=False):
        if self.test_commands:
            for command in self.test_commands['commands']:
                if command['command'] == cmd:
                    return command['output']
            raise TestCommandNotFound(
                "Mock command reponse not found for command '{0}'".format(cmd))
        if self.use_sudo and req_sudo:
            cmd = "sudo {0}".format(cmd)
        handle = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        (stdout, stderr) = handle.communicate()
        if handle.returncode > 0:
            error = "ERROR: command '{0}' failed with:\n\n{1}".format(cmd, stderr)
            print(error, file=sys.stderr)
            sys.exit(handle.returncode)
        return stdout

def main():
    parser = argparse.ArgumentParser(
        description='Collect stats related to gluster')
    parser.add_argument('--sudo',
                        help="Run gluster commands with sudo (requires NOPASSWD)",
                        action='store_true')
    parser.add_argument('--version',
                        action='version',
                        version='gluster-stats {0}'.format(__version__))
    args = parser.parse_args()

    stats = GlusterStats(use_sudo=args.sudo)
    print(json.dumps(stats.get_stats(), indent=4, sort_keys=True))

if __name__ == '__main__':
    main()
