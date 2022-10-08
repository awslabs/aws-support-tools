#!/bin/bash

########################################################################

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.


check_NVMe_in_initrd () {

find_distro=`cat /etc/os-release |sed -n 's|^ID="\([a-z]\{4\}\).*|\1|p'`      # Check if instance is using amazon AMI. 

    if [ -f /etc/redhat-release ] ; then
        # Distribution is Red hat
        lsinitrd /boot/initramfs-$(uname -r).img|grep nvme > /dev/null 2>&1
        if [ $? -ne 0 ]; then
        # NVMe module is not loaded in initrd/initramfs
        echo -e "\n\nERROR  NVMe Module is not loaded in the initramfs image.\n\t- Please run the following command on your instance to recreate initramfs:"
        echo -e '\t# sudo dracut -f -v'
        fi
    
    elif [[ "${find_distro}" == "amzn" ]]; then
        # Amazon Linux
        lsinitrd /boot/initramfs-$(uname -r).img|grep nvme > /dev/null 2>&1
        if [ $? -ne 0 ]; then
        # NVMe module is not loaded in initrd/initramfs
        echo -e "\n\nERROR  NVMe Module is not loaded in the initramfs image.\n\t- Please run the following command on your instance to recreate initramfs:"
        echo -e '\t# sudo dracut -f -v'
        fi

    elif [[ "${find_distro}" == "sles" ]] ; then
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

# See https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvme-ebs-volumes.html#timeout-nvme-ebs-volumes
# for explanation
check_nvme_timeout () {
    time_stamp=$(date +%F-%H:%M:%S)
    grub_default_file="/etc/default/grub"
    grub_config_file="/boot/grub2/grub.cfg"
    nvme_byte_timeout_value=254
    nvme_uint_timeout_value=4294967295

    if [ -f ${grub_config_file} ]; then
        if [ -n "`grep -E 'nvme.*\.io_timeout=[0-9]+' ${grub_config_file} | grep "\`uname -r\`"`" ]; then
            # NVMe io_timeout is already configured
            echo -e "\n\nOK     NVMe IO timeout configured in ${grub_config_file} for kernel `uname -r`"
            return
        fi
    fi

    if [[ "`uname -r | awk -F '.' '{print $(NF-1)}'`" =~ ^amzn* ]]; then
        # Amazon Linux 1 and 2 support nvme_core io_timeout of 4294967295
        nvme_module_name="nvme_core"
        nvme_module_value=${nvme_uint_timeout_value}
    else
        if [[ -z `modinfo nvme 2>/dev/null` &&
              -z `modinfo nvme_core 2>/dev/null` ]]; then
            # NVMe modules not installed
            echo -e "\n\nWARNING Neither nvme nor nvme_core kernel modules are loaded."
            return
        fi
        # All other Operating Systems need to be checked
        # with nvme_core taking precendence over nvme if it's available
        for module in nvme nvme_core; do
            if [[ `modinfo ${module} 2<&1 >/dev/null` ]]; then
                # module is loaded
                if [[ `modinfo -p ${module} 2>/dev/null | grep -E "^io_timeout:"` =~ (uint) ]]; then
                    # module supports io_timeout of 4294967295
                    nvme_module_name="${module}"
                    nvme_module_value=${nvme_uint_timeout_value}
                else
                    # module supports io_timeout of only 254
	            nvme_module_name="${module}"
                    nvme_module_value=${nvme_byte_timeout_value}
                fi
	    fi
        done
    fi

    if [ -f ${grub_default_file} ]; then
        if [ -n "`grep -E "nvme.*.io_timeout=" ${grub_default_file}`" ]; then
            echo -e "\n\nOK     NVMe IO timeout is already configured in ${grub_default_file}"
        else
            echo -e "\n\nWARNING  Your kernel NVMe io_timeout value is not explicitly set. You should set the io_timeout to avoid io timeout issues under Nitro."
            printf "\nEnter y to reconfigure grub to use an appropriate NVMe IO timeout.\nEnter n to keep the kernels as they are with no modification (y/n) "
            read RESPONSE;
            case "$RESPONSE" in
                [yY]|[yY][eE][sS])                                              # If answer is yes, make the changes
                        # Write changes to grub configuration
                        echo "Writing changes to /etc/default/grub and re-generating grub configuration..."
                        echo -e "\n\n***********************"
                        cp -a ${grub_default_file} ${grub_default_file}.backup.$time_stamp
                        sed -i "s/GRUB_CMDLINE_LINUX_DEFAULT=\"/GRUB_CMDLINE_LINUX_DEFAULT=\"${nvme_module_name}.io_timeout=${nvme_module_value} /" ${grub_default_file}
                        grub2-mkconfig >${grub_config_file}
                        echo -e "***********************"
                        echo -e "\nOriginal /etc/default/grub file is stored as /etc/default/grub.backup.$time_stamp"
                ;;
                [nN]|[nN][oO]|"")                                               # If answer is no, or if the user just pressed Enter
                        echo -e "Aborting: Not saving changes...\n"                  # don't save the new fstab file
                ;;
                *)                                                              # If answer is anything else, exit and don't save changes
                        echo "Invalid Response"                                 # to /etc/default/grub
                        echo "Skipping NVMe io_timeout check"
                        echo "------------------------------------------------"
                ;;
            esac
        fi
    else
        # Grub configuration not supported
        echo -e "\n\nWARNING     Could not check NVMe IO timeout. Please check grub configuration manually."
    fi

}

########################################################################

check_fstab () {
    time_stamp=$(date +%F-%H:%M:%S)
    cp /etc/fstab /etc/fstab.backup.$time_stamp
    cp /etc/fstab /etc/fstab.modified.$time_stamp
    sed -n 's|^/dev/\([sx][v]*d[a-z][0-9]*\).*|\1|p' </etc/fstab >/tmp/device_names   # Stores all /dev/sd* and /dev/xvd* entries from fstab into a temporary file
    while read LINE; do
            # For each line in /tmp/device_names
            UUID=`ls -l /dev/disk/by-uuid | grep "$LINE" | sed -n 's/^.* \([^ ]*\) -> .*$/\1/p'` # Sets the UUID name for that device
            if [ ! -z "$UUID" ]
            then
                sed -i "s|^/dev/${LINE}|UUID=${UUID}|" /etc/fstab.modified.$time_stamp               # Changes the entry in fstab to UUID form
            fi
    done </tmp/device_names

    if [ -s /tmp/device_names ]; then

        echo -e "\n\nERROR  Your fstab file contains device names. Mount the partitions using UUID's before changing an instance type to Nitro."                                                         # Outputs the new fstab file

        printf "\nEnter y to replace device names with UUID in /etc/fstab file to make it compatible for NVMe block device names.\nEnter n to keep the file as-is with no modification (y/n) "
        read RESPONSE;
        case "$RESPONSE" in
            [yY]|[yY][eE][sS])                                              # If answer is yes, keep the changes to /etc/fstab
                    echo "Writing changes to /etc/fstab..."
                    echo -e "\n\n***********************"
                    cp /etc/fstab.modified.$time_stamp /etc/fstab
                    echo -e "***********************"
                    echo -e "\nOriginal fstab file is stored as /etc/fstab.backup.$time_stamp"
                    rm /etc/fstab.modified.$time_stamp
                    ;;
            [nN]|[nN][oO]|"")                                               # If answer is no, or if the user just pressed Enter
                    echo -e "Aborting: Not saving changes...\nPrinting correct fstab file below:\n\n"                  # don't save the new fstab file
                    cat /etc/fstab.modified.$time_stamp
                    rm /etc/fstab.backup.$time_stamp
                    rm /etc/fstab.modified.$time_stamp
                    ;;
            *)                                                              # If answer is anything else, exit and don't save changes
                    echo "Invalid Response"                                 # to fstab
                    echo "Exiting"
                    rm /etc/fstab.backup.$time_stamp
                    rm /etc/fstab.modified.$time_stamp
                    exit 1
                    echo -e "------------------------------------------------"
                    ;;
    
        esac
        rm /tmp/device_names

    else
        rm /etc/fstab.backup.$time_stamp
        rm /etc/fstab.modified.$time_stamp
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

(grep 'nvme' /boot/System.map-$(uname -r)) > /dev/null 2>&1
if [ $? -ne 0 ]
    then
    # NVMe modules is not built into the kernel
    (modinfo nvme) > /dev/null 2>&1
    if [ $? -ne 0 ]
        then
        # NVMe Module is not installed. 
        echo -e "------------------------------------------------\nERROR  NVMe Module is not available on your instance. \n\t- Please install NVMe module before changing your instance type to Nitro. Look at the following link for further guidance:"
        echo -e "\t> https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvme-ebs-volumes.html"

    else
        echo -e "------------------------------------------------\n"
        echo -e "OK     NVMe Module is installed and available on your instance"
        check_NVMe_in_initrd                # Calling function to check if NVMe module is loaded in initramfs. 
    fi
else
    # NVMe modules is built into the kernel
    echo -e "------------------------------------------------\n"
    echo -e "OK     NVMe Module is installed and available on your instance"
fi

check_nvme_timeout

modinfo ena > /dev/null 2>&1
if [ $? -ne 0 ] 
    then
    # ENA Module is not installed. 
    echo -e "\n\nERROR  ENA Module is not available on your instance. \n\t- Please install ENA module before changing your instance type to Nitro. Look at the following link for further guidance:"
    echo -e "\t> https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/enhanced-networking-ena.html#enhanced-networking-ena-linux"

else 
    ena_version=`modinfo ena|grep -Eo '^version:.*' | awk '{print $2}'`
    echo -e "\n\nOK     ENA Module with version $ena_version is installed and available on your instance"

fi


check_fstab
echo -e "\n------------------------------------------------"
