#!/bin/bash

banner_text=$(cat <<EOF

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

EOF
)

# Function to check if the system is using systemd or sysvinit
check_init_system() {
    if command -v systemctl &> /dev/null; then
        echo "systemd"
    elif command -v chkconfig &> /dev/null; then
        echo "sysvinit"
    else
        echo "unknown"
    fi
}

# Function to display the description and the command output
log_command() {
    local description=$1
    local command=$2

    {
        echo -e "===== ${description} : ===== \n" 
    } >> /var/log/system_details.log 2>&1
    eval "${command}" >> /var/log/system_details.log 2>&1
    echo -e "\n\n" >> /var/log/system_details.log 2>&1
}

# Function to display the description and the command output for initramfs/initrd
log_command_initramfs() {
    local initramfs_file=$1
    local description=$2
    local command=$3

    echo -e "===== ${description} : ===== \n" >> /var/log/system_details.log 2>&1
    if [ -e "${initramfs_file}" ]; then
        eval "${command}" >> /var/log/system_details.log 2>&1
    else
       echo -e "${initramfs_file}: No such file or directory" >> /var/log/system_details.log 2>&1
    fi
    echo -e "\n\n" >> /var/log/system_details.log 2>&1
}

# Function to check which OS firewall is installed and display its rules
check_os_firewall() {
    local found_firewall=false

    # Check for iptables
    if command -v iptables &> /dev/null; then
        log_command "iptables -L -v -n" "iptables -L -v -n" 
        found_firewall=true
    fi

    # Check for firewalld
    if command -v firewall-cmd &> /dev/null; then
        log_command "firewall-cmd --list-all" "firewall-cmd --list-all" 
        found_firewall=true
    fi

    # Check for ufw
    if command -v ufw &> /dev/null; then
        log_command "ufw status verbose" "ufw status verbose" 
        found_firewall=true
    fi

    # If no firewall is found
    if [ "$found_firewall" = false ]; then

        {
            echo -e "===== Verification if one of these firewalls is installed: 'iptables', 'firewalld', 'ufw' : ===== \n" 
        } >> /var/log/system_details.log 2>&1
        echo -e "None of these firewalls ('iptables', 'firewalld', 'ufw') are installed." >> /var/log/system_details.log 2>&1
        echo -e "\n\n" >> /var/log/system_details.log 2>&1
    fi
}

# Function to check if there is any disk with size less than 1GiB
check_disks_under_1GiB() {
    # Set the minimum disk size threshold (1 GiB in bytes)
    MIN_DISK_SIZE_GiB=1073741824
    MIN_DISK_SIZE_GB=1000000000

    # Get the list of disks excluding loop devices
    disks=$(lsblk -n -o NAME,SIZE,TYPE | grep -v 'loop' | awk '$3 == "disk" {print $1, $2}')

    # Loop through each disk and check size
    while IFS= read -r line; do
        # Extract disk name and size
        disk_name=$(echo "$line" | awk '{print $1}')
        disk_size=$(echo "$line" | awk '{print $2}')

        # Skip empty disk sizes
        if [ -z "$disk_size" ]; then
            continue
        fi

        # Convert disk size to bytes (assuming human-readable format, e.g., 477G, 20M, etc.)
        disk_size_bytes=$(echo "$disk_size" | awk 'BEGIN{IGNORECASE = 1} function printpower(n,b,p) {printf "%u\n", n*b^p; next} \
        /[0-9]$/{print $1;next}; \
        /K(iB)?$/{printpower($1, 2, 10)}; \
        /M(iB)?$/{printpower($1, 2, 20)}; \
        /G(iB)?$/{printpower($1, 2, 30)}; \
        /T(iB)?$/{printpower($1, 2, 40)}; \
        /KB$/{ printpower($1, 10, 3)}; \
        /MB$/{ printpower($1, 10, 6)}; \
        /GB$/{ printpower($1, 10, 9)}; \
        /TB$/{ printpower($1, 10, 12)}')

        # Check if disk size is less than minimum threshold
        if (( disk_size_bytes < MIN_DISK_SIZE_GiB || disk_size_bytes < MIN_DISK_SIZE_GB )); then
            {
                echo "WARNING: Disk '$disk_name' has size '$disk_size', which is less than minimum threshold of 1 GiB"
            } >> /var/log/system_details.log 2>&1
            echo -e "\n\n" >> /var/log/system_details.log 2>&1
        fi
    done <<< "$disks"
}

# Function to verify the boot device 
check_boot_device() {

    { 
        echo -e "===== Boot device is : ===== \n" 
    } >> /var/log/system_details.log 2>&1

    # Run the first command to get the parent disk name
    disk_name=$(lsblk -no pkname $(df / | tail -1 | awk '{print $1}'))

    # Check if the output of the first command is empty
    if [ -z "$disk_name" ]; then
        # Run the second command if the first command's output is empty
        disk_name=$(fdisk -l | grep '^/dev/[a-z]*[0-9]' | awk '$2 == "*"')
    fi

    # Check if both commands' outputs are empty
    if [ -z "$disk_name" ]; then
        {
            echo "Script was not able to detect the boot device"
        } >> /var/log/system_details.log 2>&1
    else
        # If the first command was successful, get the full disk information
        if [ -n "$(lsblk -no pkname $(df / | tail -1 | awk '{print $1}'))" ]; then
            {
                lsblk -no NAME,MAJ:MIN,RM,SIZE,RO,TYPE | grep "^$disk_name" 
            }  >> /var/log/system_details.log 2>&1
        else
            {
                fdisk -l | grep '^/dev/[a-z]*[0-9]' | awk '$2 == "*"' >> /var/log/system_details.log 2>&1
            }  >> /var/log/system_details.log 2>&1
        fi
    fi
    echo -e "\n\n" >> /var/log/system_details.log 2>&1
}

# Display the banner
echo "$banner_text"

LOG_FILE="/var/log/system_details.log"
REP_AGENT_HOME=/var/lib/aws-replication-agent

# Ensure the script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo -e "Please execute this script using 'sudo' or with user 'root'"
    exit 1
fi

# Remove the old log file if it exists
rm -f "$LOG_FILE"

# Start gathering system details
echo -e "\n Gathering info ...\n"

echo -e "-------------------------------------\n"

{
    echo -e "Attempt $(date +"%y-%m-%d-%T")"
} >> "$LOG_FILE" 2>&1
echo -e "\n" >> "$LOG_FILE" 2>&1


echo -e "\n <<<<<<<<<<<<<<<<<<<<<<<<<< General details >>>>>>>>>>>>>>>>>>>>>>>>>> \n\n" >> "$LOG_FILE" 2>&1

log_command "cat /etc/os-release" "cat /etc/os-release"
log_command "uname -r" "uname -r"
log_command "uname -a" "uname -a"
log_command "hostnamectl" "hostnamectl"
log_command "timedatectl" "timedatectl"
log_command "chronyc tracking" "chronyc tracking"
log_command "ip a" "ip a"
log_command "route -n || ip route" "route -n || ip route"
check_os_firewall

# Check init system and log appropriate command
init_system=$(check_init_system)

if [ "$init_system" == "systemd" ]; then
    log_command "systemctl" "systemctl"
    log_command "systemctl list-unit-files --type=service --state=enabled" "systemctl list-unit-files --type=service --state=enabled"
elif [ "$init_system" == "sysvinit" ]; then
    log_command "chkconfig --list" "chkconfig --list"
else
    echo -e "Unknown init system. Skipping service list.\n" >> "$LOG_FILE" 2>&1
fi

log_command "dmidecode -t system" "dmidecode -t system"
log_command "arch" "arch"
log_command "lscpu | egrep -i Virtualization" "lscpu | egrep -i Virtualization"
log_command "last -Fxn10 shutdown reboot" "last -Fxn10 shutdown reboot"
log_command "env | grep -i proxy" "env | grep -i proxy"


echo -e "\n <<<<<<<<<<<<<<<<<<<<<<<<<< Disks / Devices / LVM / Multipath / Mount / Memory / Drivers/Modules >>>>>>>>>>>>>>>>>>>>>>>>>> \n\n" >> "$LOG_FILE" 2>&1

check_boot_device
log_command "lsblk -f" "lsblk -f"
check_disks_under_1GiB
log_command "blkid" "blkid"
log_command "fdisk -l" "fdisk -l"
log_command "parted -l" "parted -l"
log_command "fstab" "cat /etc/fstab"
log_command "pvdisplay -vv" "pvdisplay -vv"
log_command "vgdisplay -v" "vgdisplay -v"
log_command "lvdisplay -vm" "lvdisplay -vm"
log_command "ls -lartR /dev/mpath" "ls -lartR /dev/mpath"
log_command "ls -lartR /dev/mapper" "ls -lartR /dev/mapper"
log_command "multipath -ll" "multipath -ll"
log_command "powermt display dev=all" "powermt display dev=all"
log_command "mount" "mount"
log_command "mount | grep /tmp" "mount | grep /tmp"
log_command "df -hT" "df -hT"
log_command "df -hT /boot" "df -hT /boot"
log_command "df -hT /var" "df -hT /var"
log_command "df -hT /tmp" "df -hT /tmp"
log_command "free -h" "free -h"
log_command "lsmod" "lsmod"
log_command "ls -lart /dev" "ls -lart /dev"


echo -e "\n <<<<<<<<<<<<<<<<<<<<<<<<<< Directories >>>>>>>>>>>>>>>>>>>>>>>>>> \n\n"  >> "$LOG_FILE" 2>&1

log_command "ls -lah /usr/src/" "ls -lah /usr/src/"
log_command "ls -lah /usr/src/kernels/" "ls -lah /usr/src/kernels/"
log_command "ls -lah /usr/src/kernels/*" "ls -lah /usr/src/kernels/*"
log_command "ls -lah /lib/modules" "ls -lah /lib/modules"
log_command "ls -lah /lib/modules/*" "ls -lah /lib/modules/*"
log_command "ls -lah /lib/modules/*/build" "ls -lah /lib/modules/*/build"
log_command "ls -la /usr/lib/grub" "ls -la /usr/lib/grub"
log_command "ls -la /usr/share/grub2/" "ls -la /usr/share/grub2/" 
log_command "ls -la /usr/lib/grub/x86_64-efi/" "ls -la /usr/lib/grub/x86_64-efi/" 


echo -e "\n <<<<<<<<<<<<<<<<<<<<<<<<<< SELinux >>>>>>>>>>>>>>>>>>>>>>>>>> \n\n"  >> "$LOG_FILE" 2>&1

log_command "SELinux : getenforce" "getenforce"
log_command "cat /etc/sysconfig/selinux" "cat /etc/sysconfig/selinux"


echo -e "\n <<<<<<<<<<<<<<<<<<<<<<<<<< BIOS / UEFI / SecureBoot >>>>>>>>>>>>>>>>>>>>>>>>>> \n\n" >> "$LOG_FILE" 2>&1

log_command "[ -d /sys/firmware/efi ] && echo 'UEFI Boot Detected' || echo 'Legacy BIOS Boot Detected'" "[ -d /sys/firmware/efi ] && echo 'UEFI Boot Detected' || echo 'Legacy BIOS Boot Detected'"
log_command "efibootmgr -v" "efibootmgr -v"
log_command "ls -ld /sys/firmware/efi/" "ls -ld /sys/firmware/efi/"
log_command "ls -la /sys/firmware/efi/" "ls -la /sys/firmware/efi/"
log_command "ls -la /sys/firmware/efi/efivars" "ls -la /sys/firmware/efi/efivars"
log_command "/usr/bin/mokutil --sb-state || mokutil --sb-state" "/usr/bin/mokutil --sb-state || mokutil --sb-state"


echo -e " <<<<<<<<<<<<<<<<<<<<<<<<<< GRUB config files >>>>>>>>>>>>>>>>>>>>>>>>>> \n\n"  >> "$LOG_FILE" 2>&1

# Check if each GRUB configuration file exists before logging its content
grub_files=(
    "/boot/grub/grub.conf"
    "/boot/grub/grub.cfg"
    "/boot/grub2/grub.cfg"
    "/boot/grub2/grub.conf"
    "/boot/grub/menu.lst"
    "/etc/default/grub"
    "/proc/cmdline"
    "/boot/grub/grubenv"
    "/boot/grub2/grubenv"
)

for grub_file in "${grub_files[@]}"; do
    if [ -e "$grub_file" ]; then
        log_command "cat $grub_file" "cat $grub_file"
    fi
done


echo -e " <<<<<<<<<<<<<<<<<<<<<<<<<< Packages >>>>>>>>>>>>>>>>>>>>>>>>>> \n\n"   >> "$LOG_FILE" 2>&1

tools=(
    make 
    gcc 
    perl 
    tar 
    gawk
)
for tool in "${tools[@]}"; do
     log_command "$tool --version" "$tool --version"
done

log_command "python --version ; python3 --version" "python --version ; python3 --version"
log_command "rpm -aq | egrep -i 'dhclient|dhcp'" "rpm -aq | egrep -i 'dhclient|dhcp'" 
log_command "apt list --installed | egrep -i 'dhclient|dhcp' (----- Debian/Ubuntu -----)" "apt list --installed | egrep -i 'dhclient|dhcp'" 
log_command "rpm -aq | grep grub2-pc-modules" "rpm -aq | grep grub2-pc-modules"
log_command "rpm -aq | grep grub2-i386-pc (----- SUSE -----)" "rpm -aq | grep grub2-i386-pc"
log_command "apt list --installed | grep grub-pc* (----- Debian/Ubuntu -----)" "apt list --installed | grep grub-pc*" 
log_command "rpm -qa | grep mkinitrd" "rpm -qa | grep mkinitrd"
log_command "rpm -qa | grep dracut" "rpm -qa | grep dracut" 
log_command "rpm -qa | grep elfutils-libelf-devel (----- RHEL 8/CentOS 8/OL 8 -----)" "rpm -qa | grep elfutils-libelf-devel"
log_command "rpm -qa | grep xen-kmp-default (----- SUSE 11 SP4 -----)" "rpm -qa | grep xen-kmp-default" 

### Installed kernels
log_command "rpm -aq kernel" "rpm -aq kernel" 
log_command "rpm -aq | grep kernel" "rpm -aq | grep kernel"
log_command "apt list --installed | grep linux-image" "apt list --installed | grep linux-image"

### Installed kernel-devel/linux-headers
log_command "rpm -aq  | grep kernel-devel (----- RHEL/CENTOS/Oracle/AL -----)" "rpm -aq  | grep kernel-devel"
log_command "rpm -aq | grep kernel-default-devel (----- SUSE -----)" "rpm -aq | grep kernel-default-devel" 
log_command "apt list --installed | grep linux-headers (----- Debian/Ubuntu -----)" "apt list --installed | grep linux-headers" 
log_command "rpm -aq | grep kernel-uek-devel (----- Oracle with Unbreakable Enterprise Kernel -----)" "rpm -aq | grep kernel-uek-devel" 

### Available kernel-devel/linux-headers
log_command "yum list --showduplicates kernel-devel | expand (----- RHEL/CENTOS/Oracle/AL -----) " "yum list --showduplicates kernel-devel | expand"
log_command "zypper search -s kernel-default-devel* (----- SUSE -----)" "zypper search -s kernel-default-devel*"
log_command "apt-cache search linux-headers (----- Debian/Ubuntu -----)" "apt-cache search linux-headers"
log_command "yum list --showduplicates kernel-uek-devel | expand (----- Oracle with Unbreakable Enterprise Kernel -----) " "yum list --showduplicates kernel-uek-devel | expand"


echo -e " <<<<<<<<<<<<<<<<<<<<<<<<<< Initramfs/initrd/Drivers  >>>>>>>>>>>>>>>>>>>>>>>>>> \n\n"  >> "$LOG_FILE" 2>&1

# Check if lsinitramfs or lsinitrd is installed
if command -v lsinitramfs &> /dev/null; then
    INITRD_CMD="lsinitramfs"
elif command -v lsinitrd &> /dev/null; then
    INITRD_CMD="lsinitrd"
else
    echo "Neither lsinitramfs nor lsinitrd is installed..."
    exit 1
fi

grep_mod="egrep -i 'xen|nvme|ena|lvm'"

log_command "$INITRD_CMD | egrep -i 'xen|nvme|ena|lvm'" "$INITRD_CMD | $grep_mod"

log_command_initramfs "/boot/aws-launch-initramfs-$(uname -r).img" "$INITRD_CMD /boot/aws-launch-initramfs-$(uname -r).img | $grep_mod" "$INITRD_CMD /boot/aws-launch-initramfs-$(uname -r).img | $grep_mod"
log_command_initramfs "$REP_AGENT_HOME/aws-launch-initramfs-$(uname -r).img" "$INITRD_CMD $REP_AGENT_HOME/aws-launch-initramfs-$(uname -r).img | $grep_mod" "$INITRD_CMD $REP_AGENT_HOME/aws-launch-initramfs-$(uname -r).img | $grep_mod"
log_command_initramfs "/boot/aws-launch-initrd-$(uname -r)" "$INITRD_CMD /boot/aws-launch-initrd-$(uname -r) | $grep_mod (----- SUSE -----)" "$INITRD_CMD /boot/aws-launch-initrd-$(uname -r) | $grep_mod"
log_command_initramfs "$REP_AGENT_HOME/aws-launch-initrd-$(uname -r)" "$INITRD_CMD $REP_AGENT_HOME/aws-launch-initrd-$(uname -r) | $grep_mod (----- SUSE -----)" "$INITRD_CMD $REP_AGENT_HOME/aws-launch-initrd-$(uname -r) | $grep_mod"
log_command_initramfs "/boot/aws-launch-initrd.img-$(uname -r)" "$INITRD_CMD /boot/aws-launch-initrd.img-$(uname -r) | $grep_mod (----- Debian -----)" "$INITRD_CMD /boot/aws-launch-initrd.img-$(uname -r) | $grep_mod"
log_command_initramfs "$REP_AGENT_HOME/aws-launch-initrd.img-$(uname -r)" "$INITRD_CMD $REP_AGENT_HOME/aws-launch-initrd.img-$(uname -r) | $grep_mod (----- Debian -----)" "$INITRD_CMD $REP_AGENT_HOME/aws-launch-initrd.img-$(uname -r) | $grep_mod"

log_command "cat /proc/sys/kernel/modules_disabled" "cat /proc/sys/kernel/modules_disabled"
log_command "modinfo xen-netfront" "modinfo xen-netfront"
log_command "modinfo xen-blkfront" "modinfo xen-blkfront"
log_command "modinfo nvme_core" "modinfo nvme_core"
log_command "modinfo nvme" "modinfo nvme"
log_command "modinfo ena" "modinfo ena"


echo -e " <<<<<<<<<<<<<<<<<<<<<<<<<< Replication agent >>>>>>>>>>>>>>>>>>>>>>>>>> \n\n"  >> "$LOG_FILE" 2>&1

## Verify if there is an MGN or DRS replication agent installed

if [ -e "$REP_AGENT_HOME" ] ; then

        if grep -q "drs-clients" "$REP_AGENT_HOME/agent.config"; then
                echo -e "---> There is an 'AWS DRS' replication agent installed on this server <---\n\n" >> "$LOG_FILE" 2>&1
        elif grep -q "mgn-clients" "$REP_AGENT_HOME/agent.config"; then
                echo -e "---> There is an 'AWS MGN' replication agent installed on this server <---\n\n" >> "$LOG_FILE" 2>&1
        fi

        log_command "df -hT $REP_AGENT_HOME" "df -hT $REP_AGENT_HOME"
        log_command "ls -lah $REP_AGENT_HOME" "ls -lah $REP_AGENT_HOME"
        log_command "ls -lah /boot" "ls -lah /boot"
        log_command "cat $REP_AGENT_HOME/agent.config" "cat $REP_AGENT_HOME/agent.config"
        log_command "modinfo aws_replication_driver" "modinfo aws_replication_driver"
        log_command "ps -u aws-replication" "ps -u aws-replication"
        log_command "ls -l /dev | grep aws_replication" "ls -l /dev | grep aws_replication"
        log_command "lsmod | grep aws_replication_driver" "lsmod | grep aws_replication_driver"
        log_command "ps -ef | grep aws- | grep -v grep | wc -l" "ps -ef | grep aws- | grep -v grep | wc -l"
        log_command "netstat -anp | grep -i ':1500'|| ss -anp | grep -i ':1500'" "netstat -anp | grep -i ':1500' || ss -anp | grep -i ':1500'"

        if [ "$init_system" == "systemd" ]; then
            log_command "systemctl list-units --type=service | grep aws-replication" "systemctl list-units --type=service | grep aws-replication"
            log_command "systemctl status aws-replication-agent" "systemctl status aws-replication-agent"
            log_command "systemctl status aws-replication-run-migration-scripts" "systemctl status aws-replication-run-migration-scripts"
            log_command "systemctl status aws-replication-tailer" "systemctl status aws-replication-tailer"
            log_command "systemctl status aws-replication-update-volumes" "systemctl status aws-replication-update-volumes"
        fi

else
        echo -e "---> There is no AWS MGN or DRS replication agent installed on this server <---\n\n" >> "$LOG_FILE" 2>&1
fi
      

echo -e " <<<<<<<<<<<<<<<<<<<<<<<<<< Permissions >>>>>>>>>>>>>>>>>>>>>>>>>> \n\n"  >> "$LOG_FILE" 2>&1

log_command "lsattr /etc/passwd /etc/group /etc/shadow /etc/sudoers" "lsattr /etc/passwd /etc/group /etc/shadow /etc/sudoers"
log_command "grep aws-replication /etc/sudoers" "grep aws-replication /etc/sudoers"
log_command "tail -n +1 /etc/sudoers.d/*" "tail -n +1 /etc/sudoers.d/*"
log_command "ls -la /etc/sudoers.d/" "ls -la /etc/sudoers.d/"
log_command "id aws-replication" "id aws-replication"
log_command "command -v su" "command -v su"
log_command "ls -l /bin/su | ls -l /usr/bin/su" "ls -l /bin/su | ls -l /usr/bin/su"
log_command "command -v sudo" "command -v sudo"
log_command "ls -l /bin/sudo | ls -l /usr/bin/sudo" "ls -l /bin/sudo | ls -l /usr/bin/sudo"
log_command "su aws-replication -c 'id -u'" "su aws-replication -c 'id -u'"
log_command "su aws-replication -c 'sudo id -u'" "su aws-replication -c 'sudo id -u'"
log_command "lsmod | grep CE_AgentDriver" "lsmod | grep CE_AgentDriver"

echo -e " -------------------------------------"   >> "$LOG_FILE" 2>&1
echo -e " -------------------------------------"   >> "$LOG_FILE" 2>&1

echo -e "Finished gathering info \n"
echo -e "Please attach /var/log/system_details.log to the Support ticket \n"
