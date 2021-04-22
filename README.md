# piav

Program Installation Analysis using Virtualisation

## Client Setup

1. Install Python 3
2. pip install -r requirements.txt
3. Install Fibratus (https://github.com/rabbitstack/fibratus/releases)

## Virtualisation Notes

Combine split vmdks into one large VMDK:

`C:\Program Files (x86)\VMware\VMware Workstation\vmware-vdiskmanager.exe -r 'G:\Virtual Machines\PIAVWindows10IMG\Windows 10 x64-cl1.vmdk' -t 2 "G:\Virtual Machines\PIAVWindows10IMG\merged.mvdk"`

Create qcow2 from vmdk:

`qemu-img convert -f vmdk -O qcow2 .\merged.mvdk Windows10PIAVTest.qcow2`

```
qemu-system-x86_64 -cpu host -drive file=WindowsVM.img,if=virtio -net nic -net user,hostname=windowsvm -m 1G -monitor stdio -name "Windows"

qemu-system-x86_64 -cpu host -drive file=WindowsVM.img,if=virtio -net nic -net user,hostname=windowsvm -m 1G -monitor stdio -name "Windows"  -boot d -drive file=WINDOWS.iso,media=cdrom
```
