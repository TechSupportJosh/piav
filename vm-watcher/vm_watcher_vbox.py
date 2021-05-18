from virtualbox import Session, VirtualBox
from virtualbox.library import MachineState


import time
import sys

poll_time = 30

try:
    vbox = VirtualBox()
    session = Session()
except ModuleNotFoundError as e:
    if "vboxapi" in e.msg:
        print("Module 'vboxapi' is missing. Installation steps:")
        print("1. Download the VirtualBox SDK at https://www.virtualbox.org/wiki/Downloads")
        print("2. Extract ZIP")
        print("3. Navigate to installer directory")
        print("4. Run python vboxapisetup.py install")
        sys.exit(-1)
    else:
        raise e

# https://raw.githubusercontent.com/sethmlarson/virtualbox-python/984a6e2cb0e8996f4df40f4444c1528849f1c70d/virtualbox/library.py

while True:
    machines = list(filter(lambda machine: machine.name.startswith("PIAV"), vbox.machines))
    print("{} VMs found".format(len(machines)))
    for machine in machines:
        print("{}'s state: {}".format(machine.name, machine.state))
        if machine.state == MachineState.powered_off:
            # If the machine is powered off, then start it
            print("Starting machine {}".format(machine.name))
            progress = machine.launch_vm_process(session, "gui", [])
            progress.wait_for_completion()
            print("Machine {} started".format(machine.name))

    print("Sleeping...")
    time.sleep(30)