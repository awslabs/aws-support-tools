You can use this script to do the pre-requisites checks before changing the instance type to Nitro. This script performs the following actions:

    - Verify if NVMe module is installed on your instance. If yes then it will verify if it is loaded in the intiramfs image.

    - Analyses GRUB configuration and determines whether the correct NVMe IO timeout has been explicitly configured. It will give you a prompt to ask if you want to regenerate and modify your current grub configuration and insert the appropriate NVMe IO timeout. Any grub configuration files that are modified will be saved as /path/to/file.backup.$(date +%F-%H:%M:%S) for e.g /etc/default/grub.backup.2018-05-01-22:06:05. The files that are modified depend on your operating system, but the script will tell you which files it's backing up indicating the files that are being modified.

    [WARNING: Provide "y" only if you want this script to reconfigure your grub configuration files. If you provide "n" or "No", it will just skip configuring the NVMe IO timeout, and continues with the rest of the script.

    - Verify if ENA module is installed on your instance.

    - Analyses the “/etc/fstab” and look for the block devices being mounted using device names. It will give you a prompt to ask if you want to regenerate and modify your  current “/etc/fstab” file to replace the device name of each partition with its UUID. The original fstab file will be saved as /etc/fstab.backup.$(date +%F-%H:%M:%S) for e.g /etc/fstab.backup.2018-05-01-22:06:05

    [WARNING: Provide "y" only if you want this script to rewrite the current "/etc/fstab" file. If you provide "n" or "No", it will just print the correct /etc/fstab file in the output but would not replace it]


------- Running the scrips -------

- Place the script on your instance and make it executable

    # chmod +x nitro_check_script.sh

- Run the script as a "root" user or "sudo" otherwise it would fail with the following message "This script must be run as root"

    # sudo ./nitro_check_script.sh

----------------------------------
