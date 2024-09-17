# MGN DRS Linux System-Details-Tool

## Description

This script gathers various Linux system details and logs them to an output file. It is intended to be used for troubleshooting issues related to agent installation, replication, or the launch of target instances for AWS MGN and DRS.


It checks the following:

1. General System Information:
   - OS release information
   - Kernel version
   - Hostname and system time
   - Network configuration and routing
   - Firewall rules
   - System services
   - System hardware details
   - Recent shutdown and reboot history
   - Proxy environment variables

2. Disks / Devices / LVM / Multipath / Mount / Memory / Drivers/Modules:
   - Boot device
   - Block Devices and Filesystems
   - Partition Tables
   - Logical Volume Manager (LVM) details
   - Disks with size less than 1G
   - Multipath and Device Mapper Information
   - Mounted filesystems
   - Disk usage
   - Memory usage
   - Loaded kernel modules

3. Directories:
   - Kernel source directories
   - Module directories
   - GRUB configuration directories

4. SELinux:
   - SELinux status and configuration

5. BIOS / UEFI / SecureBoot:
   - Boot mode (UEFI or Legacy BIOS)
   - EFI boot manager details
   - Secure Boot status

6. GRUB Configuration Files:
   - GRUB configuration files and environment

7. Packages:
   - Required tools
   - Installed GRUB2 packages
   - Installed kernel packages
   - Installed mkinitrd and dracut packages
   - Installed and available Linux headers

8. Initramfs/initrd/Drivers:
   - Initramfs/initrd contents
   - Kernel module information

9. Replication Agent:
   - AWS replication agent details (if installed)
   - Running processes related to AWS replication Agent
   - Network connections related to AWS replication Agent

10. Permissions:
    - File attributes and permissions for critical files
    - Sudoers configuration
    - User and group information for 'aws-replication'
    - The presence and permissions of 'su' and 'sudo'


## Usage

To gather system details, create and run a shell script on your source server by following these steps:

1. Create a shell script using any text editor:

```
sudo vi system_details_parse.sh
```

2. Copy the content of the script to the file `system_details_parse.sh`

3. Change the permission of the script:

```
sudo chmod +x system_details_parse.sh
```

4. Execute the script:

```
sudo ./system_details_parse.sh
```

## Sample Output

After running the script, you will receive the following output:

```
============================================
 System Details Gathering Script
============================================
This script gathers various system details and logs them to /var/log/system_details.log.
It checks the following:

1. General System Information:
   - OS release information
   - Kernel version
   - Hostname and system time
   - Network configuration and routing
   - Firewall rules
   - System services
   - System hardware details
   - Recent shutdown and reboot history
   - Proxy environment variables

2. Disks / Devices / LVM / Multipath / Mount / Memory / Drivers/Modules:
   - Boot device
   - Block Devices and Filesystems
   - Partition Tables
   - Logical Volume Manager (LVM) details
   - Disks with size less than 1G
   - Multipath and Device Mapper Information
   - Mounted filesystems
   - Disk usage
   - Memory usage
   - Loaded kernel modules

3. Directories:
   - Kernel source directories
   - Module directories
   - GRUB configuration directories

4. SELinux:
   - SELinux status and configuration

5. BIOS / UEFI / SecureBoot:
   - Boot mode (UEFI or Legacy BIOS)
   - EFI boot manager details
   - Secure Boot status

6. GRUB Configuration Files:
   - GRUB configuration files and environment

7. Packages:
   - Required tools
   - Installed GRUB2 packages
   - Installed kernel packages
   - Installed mkinitrd and dracut packages
   - Installed and available Linux headers

8. Initramfs/initrd/Drivers:
   - Initramfs/initrd contents
   - Kernel module information

9. Replication Agent:
   - AWS replication agent details (if installed)
   - Running processes related to AWS replication Agent
   - Network connections related to AWS replication Agent

10. Permissions:
   - File attributes and permissions for critical files
   - Sudoers configuration
   - User and group information for 'aws-replication'
   - The presence and permissions of 'su' and 'sudo'
============================================

 Gathering info ...

-------------------------------------

Finished gathering info 

Please attach /var/log/system_details.log to the Support ticket 
```

## Support

Attach the output log file `/var/log/system_details.log` to [the support case](https://aws.amazon.com/contact-us/).


## Authors

- Ahmed Mansouri


&nbsp;

