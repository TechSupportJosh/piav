# piav

Program Installation Analysis using Virtualisation

## Client Setup
### Initialising the VM
By utilising disk modes within VMware/VirtualBox, we can create a VM which discards it's changes after being restarted. Therefore, the steps below are required to create a "base image". 

1. Create a new VM inside VMware:

    Use these settings (initially, use as much RAM / CPU as possible to accelerate Windows installation):
    - Name: PIAV1
    - Type: Microsoft Windows
    - Version: Windows 10 (64 bit)
    - Memory: 4096MB
    - Disk space: 45GB
  
2. Once it has booted, go through the Windows installer
   - Select I don't have a product key
   - Select Windows 10 Pro
   - Select Install Windows Only
   - Select the 45GB drive
   - Wait for it to install
   - Select Setup for personal use
   - Select Offline account
   - Select Limited experience
   - Enter piav for all username/passwords/security questions
   - Select no to all the telemetry

3. Install open vm tools and reboot

4. Disable UAC
    - Type uac into the taskbar
    - Select never notify
5. Install Python 3.9.4 with the 64-bit Windows installer (https://www.python.org/ftp/python/3.9.4/python-3.9.4-amd64.exe)
    - Ensure "Install launcher for all users" and "Add Python 3.9 to PATH" is checked
    - Disable the PATH limit length
6. Install Fibratus (https://github.com/rabbitstack/fibratus/releases)
7. Enable automatic login by following this guide https://docs.microsoft.com/en-us/troubleshoot/windows-server/user-profiles-and-logon/turn-on-automatic-logon
    - Run regedit 
    - Go to `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon`
    - Set AutoAdminLogin to `1`
    - Set DefaultUserName to `piav`
    - Create key `DefaultPassword` by doing Edit > New > String Value
    - Enter `piav` as the value

8. Copy the client directory from the  repo into C:\piav
9. cd into the piav directory
10. pip install -r requirements.txt
11. Run the pywin32 post install script (c:\users\piav\appdata\local\programs\python\python39\scripts\pywin32_postinstall.py)
12. Configure the API's URL within main.py to be the IP address of the vEthernet default switch (Windows 10 using VMware)

```
ipconfig

Ethernet adapter vEthernet (Default Switch):
Connection-specific DNS Suffix  . :
Link-local IPv6 Address . . . . . : fe80::527:2de8:fcd4:75a1%16
IPv4 Address. . . . . . . . . . . : 192.168.32.1
Subnet Mask . . . . . . . . . . . : 255.255.240.0
Default Gateway . . . . . . . . . :
```
```python
API_URL = "http://192.168.32.1:8000"
```
13.  Open task scheduler
     - Right click on Task Scheduler Library
     - Create Basic Task
     - Name it "Run PIAV"
     - Select "When I log on"
     - Select "Start a program"
     - Set "Program/script" to `C:\PIAV\run.py`
     - Set "Start in" to `C:\PIAV\`
14. Right click on the task, select Properties and "Run with highest privilege" 
15. Restart the VM and ensure that the program starts running (should be able to see /request_task in the API logs)
```
[10:54:05] <processor> Task requested however no tasks are currently waiting. (vm.py:52)
[10:54:05] <http>: 192.168.32.1:65007 - "POST /vm/request_task HTTP/1.1" 404 Not Found
[10:54:07] <processor> Task requested however no tasks are currently waiting. (vm.py:52)
[10:54:07] <http>: 192.168.32.1:65010 - "POST /vm/request_task HTTP/1.1" 404 Not Found
```
16. Shut down the VM

## Setting up VMs inside VMware
1. Change the VM specifications to 3 processor cores and 3GB of RAM
1. Right click on the VM in VMware Workstation's library panel
2. Click on Hard Drive
3. Click Advanced
4. Check Independant and select Non-persistent
5. Right click on the VM in VMware Workstation's library panel
6. Select Clone
7. Select "Create a full clone"
8. Clone the VM to another directory (this is the directory that will be passed to the VM watcher)
9. Repeat steps 21-23 for the desired number of VMs
10. Start the VM watcher `python .\vm_watcher_vmware.py G:\piavVMs "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"`

## Virtualisation Notes

Combine split vmdks into one large VMDK:

`C:\Program Files (x86)\VMware\VMware Workstation\vmware-vdiskmanager.exe -r 'G:\Virtual Machines\PIAVWindows10IMG\Windows 10 x64-cl1.vmdk' -t 2 "G:\Virtual Machines\PIAVWindows10IMG\merged.mvdk"`

Create qcow2 from vmdk:

`qemu-img convert -f vmdk -O qcow2 .\merged.mvdk Windows10PIAVTest.qcow2`

```
qemu-system-x86_64 -cpu host -drive file=WindowsVM.img,if=virtio -net nic -net user,hostname=windowsvm -m 1G -monitor stdio -name "Windows"

qemu-system-x86_64 -cpu host -drive file=WindowsVM.img,if=virtio -net nic -net user,hostname=windowsvm -m 1G -monitor stdio -name "Windows"  -boot d -drive file=WINDOWS.iso,media=cdrom
```
