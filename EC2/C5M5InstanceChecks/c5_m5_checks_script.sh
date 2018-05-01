#!/bin/bash

########################################################################

check_NVMe_in_initrd () {

is_amazon=`cat /etc/os-release |sed -n 's|^ID="\([a-z]\{4\}\).*|\1|p'`      # Check if instance is using amazon AMI. 

    if [ -f /etc/redhat-release ] ; then
        # Distribution is Red hat
        lsinitrd /boot/initramfs-$(uname -r).img|grep nvme > /dev/null 2>&1
        if [ $? -ne 0 ]; then
        # NVMe module is not loaded in initrd/initramfs
        echo -e "\n\nERROR  NVMe Module is not loaded in the initramfs image.\n\t- Please run the following command on your instance to recreate initramfs:"
        echo -e '\t# sudo dracut -f -v'
        fi
    
    elif [[ "${is_amazon}" == "amzn" ]]; then
        # Amazon Linux
        lsinitrd /boot/initramfs-$(uname -r).img|grep nvme > /dev/null 2>&1
        if [ $? -ne 0 ]; then
        # NVMe module is not loaded in initrd/initramfs
        echo -e "\n\nERROR  NVMe Module is not loaded in the initramfs image.\n\t- Please run the following command on your instance to recreate initramfs:"
        echo -e '\t# sudo dracut -f -v'
        fi

    elif [ -f /etc/SuSE-release ] ; then
        # Distribution is SuSe Linux
        lsinitrd /boot/initrd-$(uname -r)|grep nvme > /dev/null 2>&1
        if [ $? -ne 0 ]; then
        # NVMe module is not loaded in initrd/initramfs
        echo -e "\n\nERROR  NVMe Module is not loaded in the initramfs image.\n\t- Please run the following command on your instance to recreate initramfs:"
        echo -e '\t# sudo dracut -f -v'
        fi
        
    elif [ -f /etc/debian_version ] ; then
        # Distribution is debian based(Debian/Ubuntu)
        lsinitramfs /boot/initrd.img-$(uname -r)|grep nvme > /dev/null 2>&1
        if [ $? -ne 0 ]; then
        # NVMe module is not loaded in initrd/initramfs
        echo -e "\n\nERROR  NVMe Module is not loaded in the initramfs image.\n\t- Please run the following command on your instance to recreate initramfs:"
        echo -e '\t# sudo update-initramfs -c -k all'
        fi

    else 
        echo -e "\n\nUnsupported OS for this script."
        echo -e "\n\n------------------------------------------------"
        exit 1
    fi
}
########################################################################

check_fstab () {
    time_stamp=$(date +%F-%H:%M:%S)
    cp /etc/fstab /etc/fstab.backup.$time_stamp
    sed -n 's|^/dev/\([sx][v]*d[a-z][0-9]*\).*|\1|p' </etc/fstab >/tmp/device_names   # Stores all /dev/sd* and /dev/xvd* entries from fstab into a temporary file
    while read LINE; do
            # For each line in /tmp/device_names
            UUID=`ls -l /dev/disk/by-uuid | grep "$LINE" | sed -n 's/^.* \([^ ]*\) -> .*$/\1/p'` # Sets the UUID name for that device
            if [ ! -z "$UUID" ]
            then
                sed -i "s|^/dev/${LINE}|UUID=${UUID}|" /etc/fstab               # Changes the entry in fstab to UUID form
            fi
    done </tmp/device_names

    if [ -s /tmp/device_names ]; then

        echo -e "\n\nERROR  Your fstab file contains device names. Mount the partitions using UUID's before changing an instance type to M5/C5."                                                         # Outputs the new fstab file
        printf "\nPress y to replace device names with UUID in your fstab file? (y/n) "
        read RESPONSE;
        case "$RESPONSE" in
            [yY]|[yY][eE][sS])                                              # If answer is yes, keep the changes to /etc/fstab
                    echo "Writing changes to /etc/fstab..."
                    echo -e "\n\n***********************"
                    cat /etc/fstab
                    echo -e "***********************"
                    echo -e "\nOriginal fstab file is stored as /etc/fstab.backup.$time_stamp"
                    ;;
            [nN]|[nN][oO]|"")                                               # If answer is no, or if the user just pressed Enter
                    echo -e "Aborting: Not saving changes...\nPrinting correct fstab file below:"                  # don't save the new fstab file
                    cat /etc/fstab
                    cp /etc/fstab.backup.$time_stamp /etc/fstab
                    rm /etc/fstab.backup.$time_stamp
                    ;;
            *)                                                              # If answer is anything else, exit and don't save changes
                    echo "Invalid Response"                                 # to fstab
                    echo "Exiting"
                    cp /etc/fstab.backup.$time_stamp /etc/fstab
                    rm /etc/fstab.backup.$time_stamp
                    exit 1
                    echo -e "------------------------------------------------"
                    ;;
    
        esac
        rm /tmp/device_names

    else 
        echo -e "\n\nOK     fstab file looks fine and does not contain any device names. "
    fi

}

########################################################################


# Main code starts from here

PATH=/bin:/sbin:/usr/bin:/usr/sbin

if [ `id -u` -ne 0 ]; then                                              # Checks to see if script is run as root
        echo -e "------------------------------------------------"
        echo -e "\nThis script must be run as root" >&2                 # If it isn't, exit with error
        echo -e "\n------------------------------------------------"
        exit 1
fi

modinfo nvme > /dev/null 2>&1
if [ $? -ne 0 ]
    then
    # NVMe Module is not installed. 
    echo -e "------------------------------------------------\nERROR  NVMe Module is not available on your instance. \n\t- Please install NVMe module before changing your instance type to M5/C5. Look at the following link for further guidance:"
    echo -e "\t> https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvme-ebs-volumes.html"

else 
    echo -e "------------------------------------------------\n"
    echo -e "OK     NVMe Module is installed and available on your instance"
    check_NVMe_in_initrd                # Calling function to check if NVMe module is loaded in initramfs. 
fi


modinfo ena > /dev/null 2>&1
if [ $? -ne 0 ] 
    then
    # ENA Module is not installed. 
    echo -e "\n\nERROR  ENA Module is not available on your instance. \n\t- Please install ENA module before changing your instance type to M5/C5. Look at the following link for further guidance:"
    echo -e "\t> https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/enhanced-networking-ena.html#enhanced-networking-ena-linux"

else 
    ena_version=`modinfo ena|grep -Eo '^version:.*' | awk '{print $2}'`
    echo -e "\n\nOK     ENA Module with version $ena_version is installed and available on your instance"

fi


check_fstab
echo -e "\n------------------------------------------------"

