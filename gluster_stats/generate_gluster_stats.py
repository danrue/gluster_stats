#!/usr/bin/env python

from __future__ import print_function
import json
import subprocess

from builtins import object, str

PER_VOLUME_COMMANDS = [
    "gluster volume heal {0} info",
    "gluster volume heal {0} info split-brain",
    "gluster volume status {0} detail",
]

def execute(cmd):
    handle = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    (stdout, stderr) = handle.communicate()
    return {'command': cmd, 'output': stdout+stderr}

def main():
    commands = []
    command = "gluster --version"
    commands.append(execute(command))

    gluster_version = commands[-1]['output'].split()[1]

    command = "gluster peer status"
    commands.append(execute(command))

    command = "gluster volume list"
    commands.append(execute(command))

    for volume in commands[-1]['output'].split():
        for command in PER_VOLUME_COMMANDS:
            output = execute(command.format(volume))
            if 'heal' in command:
                # Strip file list as they may be private data
                safe_output = []
                for line in output['output'].split('\n'):
                    if line.startswith("Number"):
                        safe_output.append(line)
                output['output'] = '\n'.join(safe_output)
            commands.append(output)

    command = "pidof glusterd"
    commands.append(execute(command))

    command = "pidof glusterfsd"
    commands.append(execute(command))

    output = {'gluster_version': gluster_version, 'commands': commands}
    with open("gluster_stats_{0}.json".format(gluster_version), 'w') as f:
        f.write(json.dumps(output, indent=4, sort_keys=True))

if __name__ == '__main__':
    main()
