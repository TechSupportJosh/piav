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

8. pip install -r requirements.txt

## Virtualisation Notes

Combine split vmdks into one large VMDK:

`C:\Program Files (x86)\VMware\VMware Workstation\vmware-vdiskmanager.exe -r 'G:\Virtual Machines\PIAVWindows10IMG\Windows 10 x64-cl1.vmdk' -t 2 "G:\Virtual Machines\PIAVWindows10IMG\merged.mvdk"`

Create qcow2 from vmdk:

`qemu-img convert -f vmdk -O qcow2 .\merged.mvdk Windows10PIAVTest.qcow2`

```
qemu-system-x86_64 -cpu host -drive file=WindowsVM.img,if=virtio -net nic -net user,hostname=windowsvm -m 1G -monitor stdio -name "Windows"

qemu-system-x86_64 -cpu host -drive file=WindowsVM.img,if=virtio -net nic -net user,hostname=windowsvm -m 1G -monitor stdio -name "Windows"  -boot d -drive file=WINDOWS.iso,media=cdrom
```
