#!/usr/bin/env python3

import subprocess
import argparse
import os
import time
from pathlib import Path

# https://stackoverflow.com/a/51212150
def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)


parser = argparse.ArgumentParser(
    description="Watch PIAV VMs for when they power down, as to automatically restart them."
)
parser.add_argument("vm_directory", type=dir_path, help="Directory containing all VMs")
parser.add_argument("vmrun_path", type=file_path, help="Path to the vmrun executable")
parser.add_argument(
    "--poll-time", type=int, help="How often are VM statuses polled", default=30
)

args = parser.parse_args()


def get_running_machine_paths():
    running_machines = []

    response = subprocess.check_output([args.vmrun_path, "list"])
    for line in response.decode("utf-8").split("\n"):
        line = line.rstrip()
        if line and not line.startswith("Total running VMs:"):
            running_machines.append(line)

    return running_machines


def start_machine(vmx_path):
    print("Starting {}".format(vmx_path))
    try:
        output = subprocess.check_output([args.vmrun_path, "start", vmx_path])
    except subprocess.CalledProcessError:
        print("Failed to start machine {}".format(vmx_path))
    else:
        print("Started machine {}".format(vmx_path))


print("Searching for VMs inside {}".format(args.vm_directory))

machines = []

for path in Path(args.vm_directory).rglob("*.vmx"):
    if path.parent.name.startswith("PIAV"):
        machines.append(str(path))

print(" ")
print("Found machines:")
for machine in machines:
    print(machine)
print(" ")

try:
    while True:
        print("Polling machines...")
        running_machines = get_running_machine_paths()
        for machine in machines:
            if machine not in running_machines:
                start_machine(machine)
        time.sleep(args.poll_time)
except KeyboardInterrupt:
    print("Stopping watching...")
