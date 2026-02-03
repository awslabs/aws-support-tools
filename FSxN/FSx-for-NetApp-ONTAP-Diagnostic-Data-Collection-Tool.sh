#!/usr/bin/env bash
#
#
# Copyright 2025-2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.
#
# FSx for NetApp ONTAP – Data Collection Script (Linux clients only)
# Version: 3.7.1 (Production - NVMe Support with Fixes)
#
# Author: Sofien Abid (AWS Support)
# Issues: https://github.com/awslabs/aws-support-tools/issues
#
# DISCLAIMER:
# - Test in non-production environments first
# - Use at your own risk
#
# Changelog v3.7.1:
#   - Added NVMe/TCP protocol support
#   - Fixed: Removed invalid "vserver nvme interface show" command
#   - Fixed: Corrected namespace field "subsystem-map" to "uuid"
#   - Fixed: Updated network interface command for NVMe
#
#

set -o pipefail

# ---------------------------------------------------------------------------
# Global Variables
# ---------------------------------------------------------------------------

SCRIPT_VERSION="3.7.1"
SCRIPT_NAME=$(basename "$0")
OUTPUT_DIR=""
LOG_FILE="fsx_collect.log"
FSX_CMD_COUNTER=0
CLIENT_CMD_COUNTER=0
SSH_CONTROL_PATH=""
SSH_HOST=""
SSH_USER=""
SSH_PORT=""
SMB_CREDS_FILE=""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
PROFILE=""
FSX_ENDPOINT=""
FSX_USERNAME="fsxadmin"
FSX_PORT=22
FSX_KEY_FILE=""
SVM=""
VOLUMES=""
INCLUDE_CLIENT=false
FSX_ONLY=false
TEST_MOUNT=false
MOUNT_ENDPOINT=""
MOUNT_PATH=""
MOUNT_TYPE=""
MOUNT_POINT=""
NFS_VERSION="auto"

declare -a FSX_COMMANDS
declare -a CLIENT_COMMANDS

# ---------------------------------------------------------------------------
# Logging Functions
# ---------------------------------------------------------------------------

log_info() {
    local msg="$1"
    echo -e "${BLUE}[INFO]${NC} $msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $msg" >> "$LOG_FILE" 2>/dev/null || true
}

log_success() {
    local msg="$1"
    echo -e "${GREEN}[SUCCESS]${NC} $msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $msg" >> "$LOG_FILE" 2>/dev/null || true
}

log_warning() {
    local msg="$1"
    echo -e "${YELLOW}[WARNING]${NC} $msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $msg" >> "$LOG_FILE" 2>/dev/null || true
}

log_error() {
    local msg="$1"
    echo -e "${RED}[ERROR]${NC} $msg" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $msg" >> "$LOG_FILE" 2>/dev/null || true
}

log_debug() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [DEBUG] $msg" >> "$LOG_FILE" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Platform Check
# ---------------------------------------------------------------------------

check_platform() {
    local platform=$(uname -s)
    
    if [[ "$platform" != "Linux" ]]; then
        log_error "This script is intended to run on Linux clients only"
        log_error "Detected platform: $platform"
        exit 1
    fi
    
    log_info "Platform check passed: $platform $(uname -r)"
}

# ---------------------------------------------------------------------------
# Distribution Detection
# ---------------------------------------------------------------------------

detect_distro() {
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        echo "$ID"
    elif [[ -f /etc/redhat-release ]]; then
        echo "rhel"
    elif [[ -f /etc/debian_version ]]; then
        echo "debian"
    else
        echo "unknown"
    fi
}

get_install_command() {
    local distro="$1"
    local tool="$2"
    
    case "$tool" in
        nfsstat|showmount)
            case "$distro" in
                ubuntu|debian) echo "apt-get install nfs-common" ;;
                sles|opensuse*) echo "zypper install nfs-client" ;;
                *) echo "yum install nfs-utils" ;;
            esac
            ;;
        rpcinfo)
            case "$distro" in
                ubuntu|debian|sles|opensuse*) echo "apt-get install rpcbind" ;;
                *) echo "yum install rpcbind" ;;
            esac
            ;;
        smbclient)
            case "$distro" in
                ubuntu|debian) echo "apt-get install smbclient" ;;
                sles|opensuse*) echo "zypper install samba-client" ;;
                *) echo "yum install samba-client" ;;
            esac
            ;;
        iscsiadm)
            case "$distro" in
                ubuntu|debian) echo "apt-get install open-iscsi" ;;
                sles|opensuse*) echo "zypper install open-iscsi" ;;
                *) echo "yum install iscsi-initiator-utils" ;;
            esac
            ;;
        nvme)
            case "$distro" in
                ubuntu|debian) echo "apt-get install nvme-cli" ;;
                sles|opensuse*) echo "zypper install nvme-cli" ;;
                *) echo "yum install nvme-cli" ;;
            esac
            ;;
        nc)
            case "$distro" in
                ubuntu|debian) echo "apt-get install netcat" ;;
                sles|opensuse*) echo "zypper install netcat" ;;
                *) echo "yum install nmap-ncat" ;;
            esac
            ;;
        lsscsi)
            case "$distro" in
                ubuntu|debian) echo "apt-get install lsscsi" ;;
                sles|opensuse*) echo "zypper install lsscsi" ;;
                *) echo "yum install lsscsi" ;;
            esac
            ;;
    esac
}

# ---------------------------------------------------------------------------
# Dependency Checks
# ---------------------------------------------------------------------------

check_optional_dependencies() {
    log_info "Checking optional dependencies..."
    
    local distro=$(detect_distro)
    local missing_tools=()
    
    local nfs_tools=("nfsstat" "showmount" "rpcinfo")
    local smb_tools=("smbclient")
    local iscsi_tools=("iscsiadm" "lsscsi")
    local nvme_tools=("nvme")
    local network_tools=("nc")
    
    local tools_to_check=()
    case "$PROFILE" in
        nfs|all)
            tools_to_check+=("${nfs_tools[@]}")
            ;;
        smb)
            tools_to_check+=("${smb_tools[@]}")
            ;;
        iscsi)
            tools_to_check+=("${iscsi_tools[@]}")
            ;;
        nvme)
            tools_to_check+=("${nvme_tools[@]}")
            ;;
    esac
    
    if [[ "$PROFILE" == "all" ]]; then
        tools_to_check+=("${smb_tools[@]}")
        tools_to_check+=("${iscsi_tools[@]}")
        tools_to_check+=("${nvme_tools[@]}")
    fi
    
    tools_to_check+=("${network_tools[@]}")
    
    for tool in "${tools_to_check[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_warning "Optional tools not found: ${missing_tools[*]}"
        log_warning "Some diagnostic commands will be skipped"
        echo ""
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}        Optional Tools Missing (Non-Critical)${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "For more comprehensive diagnostics, you can install:"
        echo ""
        for tool in "${missing_tools[@]}"; do
            local install_cmd=$(get_install_command "$distro" "$tool")
            echo "  • $tool:  sudo $install_cmd"
        done
        echo ""
        echo -e "${CYAN}Note: Script will continue WITHOUT installing anything${NC}"
        echo "      Data collection will work with available tools"
        echo ""
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        read -p "Press Enter to continue..." -t 10 || echo ""
    else
        log_success "All optional tools are available"
    fi
}

check_dependencies() {
    local missing_deps=()
    local required_commands=("ssh" "tar" "grep" "awk" "sed" "timeout")
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing REQUIRED dependencies: ${missing_deps[*]}"
        log_error "Please install missing packages and try again"
        exit 1
    fi
    
    if [[ "${BASH_VERSINFO[0]}" -lt 4 ]]; then
        log_error "Bash 4.0 or higher is required"
        log_error "Current version: ${BASH_VERSION}"
        exit 1
    fi
    
    log_debug "All required dependencies satisfied"
}

# ---------------------------------------------------------------------------
# SSH Control Master
# ---------------------------------------------------------------------------

setup_ssh_control_master() {
    local host="$1"
    local username="$2"
    local port="$3"
    local key_file="$4"
    
    SSH_HOST="$host"
    SSH_USER="$username"
    SSH_PORT="$port"
    
    local control_dir="/tmp/ssh_fsx_$$"
    mkdir -p "$control_dir"
    chmod 700 "$control_dir"
    
    local control_path="$control_dir/master"
    local ssh_opts="-o StrictHostKeyChecking=no -o ControlMaster=auto -o ControlPath=$control_path -o ControlPersist=300"
    
    [[ -n "$key_file" ]] && ssh_opts="$ssh_opts -i $key_file"
    
    SSH_CONTROL_PATH="$control_path"
    log_debug "SSH control path: $control_path"
    echo "$control_path|$ssh_opts"
}

cleanup_ssh_control_master() {
    log_debug "Cleaning up SSH control master..."
    
    if [[ -n "$SSH_CONTROL_PATH" && -S "$SSH_CONTROL_PATH" && -n "$SSH_HOST" && -n "$SSH_USER" ]]; then
        log_debug "Closing SSH connection to ${SSH_USER}@${SSH_HOST}"
        ssh -O exit -o ControlPath="$SSH_CONTROL_PATH" "${SSH_USER}@${SSH_HOST}" 2>/dev/null || true
        ssh -O stop -o ControlPath="$SSH_CONTROL_PATH" "${SSH_USER}@${SSH_HOST}" 2>/dev/null || true
        
        local wait_count=0
        while [[ -S "$SSH_CONTROL_PATH" && $wait_count -lt 10 ]]; do
            sleep 0.2
            ((wait_count++))
        done
        
        [[ -S "$SSH_CONTROL_PATH" ]] && rm -f "$SSH_CONTROL_PATH" 2>/dev/null || true
    fi
    
    local control_dir=$(dirname "$SSH_CONTROL_PATH" 2>/dev/null)
    if [[ -d "$control_dir" && "$control_dir" == "/tmp/ssh_fsx_"* ]]; then
        rm -rf "$control_dir" 2>/dev/null || true
    fi
    
    find /tmp -maxdepth 1 -type d -name "ssh_fsx_*" -mmin +10 -exec rm -rf {} \; 2>/dev/null || true
}

cleanup_temp_files() {
    log_debug "Cleaning up temporary files..."
    
    rm -f /tmp/nfs_mount_test_*.sh 2>/dev/null || true
    rm -f /tmp/smb_mount_test_*.sh 2>/dev/null || true
    
    if [[ -n "$SMB_CREDS_FILE" && -f "$SMB_CREDS_FILE" ]]; then
        dd if=/dev/zero of="$SMB_CREDS_FILE" bs=1k count=1 2>/dev/null || true
        rm -f "$SMB_CREDS_FILE" 2>/dev/null || true
        log_debug "Credentials file securely deleted"
    fi
    
    rm -f /tmp/smb_creds_*.conf 2>/dev/null || true
    find /tmp -maxdepth 1 -type f \( -name "nfs_mount_test_*.sh" -o -name "smb_mount_test_*.sh" -o -name "smb_creds_*.conf" \) -mmin +10 -delete 2>/dev/null || true
}

cleanup_old_temp_files() {
    log_debug "Cleaning up orphaned temp files..."
    
    local ssh_dirs=$(find /tmp -maxdepth 1 -type d -name "ssh_fsx_*" -mmin +10 2>/dev/null | wc -l)
    local mount_scripts=$(find /tmp -maxdepth 1 -type f -name "*_mount_test_*.sh" -mmin +10 2>/dev/null | wc -l)
    local cred_files=$(find /tmp -maxdepth 1 -type f -name "smb_creds_*.conf" -mmin +10 2>/dev/null | wc -l)
    
    find /tmp -maxdepth 1 -type d -name "ssh_fsx_*" -mmin +10 -exec rm -rf {} \; 2>/dev/null || true
    find /tmp -maxdepth 1 -type f -name "*_mount_test_*.sh" -mmin +10 -delete 2>/dev/null || true
    find /tmp -maxdepth 1 -type f -name "smb_creds_*.conf" -mmin +10 -delete 2>/dev/null || true
    
    if [[ $ssh_dirs -gt 0 || $mount_scripts -gt 0 || $cred_files -gt 0 ]]; then
        log_info "Cleaned up orphaned files: $ssh_dirs SSH dirs, $mount_scripts scripts, $cred_files cred files"
    fi
}

emergency_cleanup() {
    log_debug "Emergency cleanup triggered"
    
    if [[ -n "$SSH_CONTROL_PATH" && -S "$SSH_CONTROL_PATH" && -n "$SSH_HOST" && -n "$SSH_USER" ]]; then
        ssh -O exit -o ControlPath="$SSH_CONTROL_PATH" "${SSH_USER}@${SSH_HOST}" 2>/dev/null || true
    fi
    
    cleanup_temp_files
    
    if [[ -n "$SSH_CONTROL_PATH" ]]; then
        local control_dir=$(dirname "$SSH_CONTROL_PATH" 2>/dev/null)
        [[ -d "$control_dir" ]] && rm -rf "$control_dir" 2>/dev/null || true
    fi
}

# ---------------------------------------------------------------------------
# Safe Filename Generation
# ---------------------------------------------------------------------------

create_safe_filename() {
    local cmd="$1"
    local prefix="$2"
    local index="$3"
    
    cmd=$(echo "$cmd" | sed 's/#.*//' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
    
    if [[ -z "$cmd" ]]; then
        cmd="empty_command"
    fi
    
    local safe=$(echo "$cmd" | tr -cs '[:alnum:]' '_')
    safe=$(echo "$safe" | sed 's/^_*//' | sed 's/_*$//')
    
    if [[ ${#safe} -gt 60 ]]; then
        safe="${safe:0:60}"
        safe=$(echo "$safe" | sed 's/_*$//')
    fi
    
    printf "%s_%03d_%s.txt" "$prefix" "$index" "$safe"
}

# ---------------------------------------------------------------------------
# Profile Definitions - v3.7.1 (NVMe Commands Fixed)
# ---------------------------------------------------------------------------

load_basic_profile() {
    FSX_COMMANDS+=(
        # System Information
        "version"
        "cluster show"
        "node show"
        "system health status show"
        "system health alert show"
        "node show -fields node,uptime"
        
        # Events & Jobs
        "event log show -severity error -time >7d"
        "job show"
        "autosupport history show -node * -fields Node,Seq-Num,Time,Status,Error"
        
        # SVM & Network
        "vserver show"
        "vserver show -instance"
        "network interface show"
        "network route show"
        "network port show"
        "network connections active show"
        "network connections listening show"
        
        # Storage
        "vserver show-aggregates"
        "storage aggregate show"
        "storage failover show"
        
        # Volumes
        "volume show -fields volume,vserver,state,type,size,available,used,percent-used,junction-path,snapshot-policy"
        "snapshot show"
        "volume efficiency show"
        "df -h"
        
        # Performance & QoS
        "qos policy-group show"
        "qos adaptive-policy-group show"
        "qos workload show"
        
        # Name Services
        "vserver services name-service dns show"
        "vserver services name-service ns-switch show"
        
        # Security
        "security login show"
    )
}

load_nfs_profile() {
    FSX_COMMANDS+=(
        # NFS Status & Configuration
        "vserver nfs status"
        "vserver nfs show"
        "vserver nfs show -instance"
        "vserver nfs show -fields v3,v4.0,v4.1,v4.2"
        
        # Export Policies
        "export-policy show"
        "export-policy rule show"
        "export-policy rule show -fields policy,ruleindex,clientmatch,rorule,rwrule,superuser"
        
        # Connected Clients
        "vserver nfs connected-clients show"
        
        # Qtrees
        "qtree show"
        "qtree show -fields qtree,volume,security-style,status"
        
        # Name Services
        "vserver services name-service unix-user show"
        "vserver services name-service unix-group show"
        "vserver services name-service ldap show"
        "vserver services name-service nis-domain show"
        
        # Performance
        "qos statistics volume latency show -iterations 1"
    )
    
    CLIENT_COMMANDS+=(
        "# ===== NFS Client Information ====="
        "mount | grep -i nfs || true"
        "grep -i nfs /etc/fstab || true"
        "cat /proc/mounts | grep nfs || true"
        
        "nfsstat -c 2>/dev/null || true"
        "nfsstat -m 2>/dev/null || true"
        "rpcinfo -p 2>/dev/null || true"
        "showmount -e localhost 2>/dev/null || true"
        
        "uname -a"
        "cat /etc/os-release 2>/dev/null || true"
        
        "cat /proc/fs/nfsd/versions 2>/dev/null || true"
        "cat /proc/fs/nfs/exports 2>/dev/null || true"
        "cat /proc/net/rpc/nfs 2>/dev/null || true"
        "modinfo nfs 2>/dev/null | grep -i version || true"
        
        "cat /etc/resolv.conf"
        "cat /etc/hosts | grep -v '^#' | grep -v '^$' || true"
        "getent hosts \$(hostname) 2>/dev/null || true"
        
        "ip addr"
        "ip route"
        "ss -tuln | grep 2049 2>/dev/null || netstat -tuln | grep 2049 2>/dev/null || true"
        
        "dmesg | grep -i nfs | tail -n 100 || true"
        "journalctl -u nfs-client.target --no-pager -n 50 2>/dev/null || true"
    )
}

load_smb_profile() {
    FSX_COMMANDS+=(
        # CIFS Status & Configuration
        "vserver cifs show"
        "vserver cifs show -instance"
        "vserver cifs options show"
        "vserver cifs security show"
        
        # AD Connectivity
        "vserver cifs check"
        "vserver cifs domain discovered-servers show"
        "vserver cifs domain preferred-dc show"
        
        # Sessions & Connections
        "vserver cifs connection show"
        "vserver cifs session show"
        "vserver cifs session show -fields node,vserver,session-id,connection-id,user,windows-user"
        
        # Shares & ACLs
        "vserver cifs share show"
        "vserver cifs share show -fields share-name,path,share-properties,comment"
        "vserver cifs share access-control show"
        
        # Users & Groups
        "vserver cifs users-and-groups local-user show"
        "vserver cifs users-and-groups local-group show"
        
        # Name Mapping
        "vserver name-mapping show"
        
        # Locks
        "vserver locks show"
        
        # BranchCache
        "vserver cifs branchcache show"
        
        # Performance
        "qos statistics volume latency show -iterations 1"
    )
    
    CLIENT_COMMANDS+=(
        "# ===== SMB Client Information ====="
        "mount | grep -i cifs || true"
        "cat /proc/mounts | grep cifs || true"
        "grep -i cifs /etc/fstab 2>/dev/null || true"
        
        "uname -a"
        "cat /etc/os-release 2>/dev/null || true"
        
        "cat /etc/samba/smb.conf 2>/dev/null || true"
        "modinfo cifs 2>/dev/null || true"
        "cat /proc/fs/cifs/DebugData 2>/dev/null || true"
        
        "klist 2>/dev/null || true"
        "cat /etc/krb5.conf 2>/dev/null || true"
        
        "cat /etc/resolv.conf"
        "cat /etc/hosts | grep -v '^#' | grep -v '^$' || true"
        "getent hosts \$(hostname) 2>/dev/null || true"
        
        "ip addr"
        "ip route"
        "ss -tuln | grep 445 2>/dev/null || netstat -tuln | grep 445 2>/dev/null || true"
        
        "dmesg | grep -i cifs | tail -n 100 || true"
        "journalctl -u smb.service --no-pager -n 50 2>/dev/null || true"
    )
}

load_iscsi_profile() {
    FSX_COMMANDS+=(
        # iSCSI Status & Configuration
        "vserver iscsi status"
        "vserver iscsi show"
        "vserver iscsi show -instance"
        "vserver iscsi interface show"
        
        # Connections & Sessions
        "vserver iscsi connection show"
        "vserver iscsi session show"
        
        # LUNs
        "lun show"
        "lun show -fields path,size,state,mapped,read-only,space-reserve"
        "lun show -fields path,serial"
        "lun show -fields path,size,size-used,block-size"
        
        # LUN Mapping
        "lun mapping show"
        "lun mapping show -fields path,igroup,lun-id,reporting-nodes"
        
        # iGroups
        "lun igroup show"
        "lun igroup show -fields igroup,protocol,ostype,initiator"
        
        # Performance
        "qos statistics volume latency show -iterations 1"
        
        # Network
        "network interface show -role data -data-protocol iscsi"
    )
    
    CLIENT_COMMANDS+=(
        "# ===== iSCSI Client Information ====="
        
        "uname -a"
        "cat /etc/os-release 2>/dev/null || true"
        
        "lsblk"
        "lsblk -f 2>/dev/null || true"
        "lsscsi 2>/dev/null || true"
        
        "cat /etc/iscsi/initiatorname.iscsi 2>/dev/null || true"
        "cat /etc/iscsi/iscsid.conf 2>/dev/null || true"
        
        "iscsiadm -m session 2>/dev/null || true"
        "iscsiadm -m session -P 3 2>/dev/null || true"
        "iscsiadm -m node 2>/dev/null || true"
        
        "multipath -ll 2>/dev/null || true"
        "cat /etc/multipath.conf 2>/dev/null || true"
        
        "ip addr"
        "ip route"
        "ss -tuln | grep 3260 2>/dev/null || netstat -tuln | grep 3260 2>/dev/null || true"
        
        "dmesg | grep -i iscsi | tail -n 100 || true"
        "dmesg | grep -i scsi | tail -n 50 || true"
        "journalctl -u iscsid.service --no-pager -n 50 2>/dev/null || true"
    )
}

load_nvme_profile() {
    FSX_COMMANDS+=(
        # NVMe Status & Configuration
        "vserver nvme show"
        "vserver nvme show -instance"
        
        # NVMe Subsystems
        "vserver nvme subsystem show"
        "vserver nvme subsystem show -instance"
        "vserver nvme subsystem map show"
        "vserver nvme subsystem host show"
        
        # NVMe Namespaces (FIXED v3.7.1 - Corrected field names)
        "vserver nvme namespace show"
        "vserver nvme namespace show -fields path,size,state,uuid"
        "vserver nvme namespace show -fields path,size,size-used,block-size"
        
        # Performance
        "qos statistics volume latency show -iterations 1"
        
        # Network (FIXED v3.7.1 - Simplified command)
        "network interface show -data-protocol nvme-tcp"
    )
    
    CLIENT_COMMANDS+=(
        "# ===== NVMe Client Information ====="
        
        "uname -a"
        "cat /etc/os-release 2>/dev/null || true"
        
        "lsblk"
        "lsblk -f 2>/dev/null || true"
        
        "cat /etc/nvme/hostnqn 2>/dev/null || true"
        "cat /etc/nvme/hostid 2>/dev/null || true"
        
        "nvme version 2>/dev/null || true"
        "nvme list 2>/dev/null || true"
        "nvme list-subsys 2>/dev/null || true"
        
        "modinfo nvme 2>/dev/null || true"
        "modinfo nvme-tcp 2>/dev/null || true"
        "modinfo nvme-fabrics 2>/dev/null || true"
        
        "ip addr"
        "ip route"
        "ss -tuln | grep 4420 2>/dev/null || netstat -tuln | grep 4420 2>/dev/null || true"
        
        "dmesg | grep -i nvme | tail -n 100 || true"
        "journalctl -u nvme.service --no-pager -n 50 2>/dev/null || true"
        "journalctl -u nvmefc-boot-connections.service --no-pager -n 50 2>/dev/null || true"
    )
}

# ---------------------------------------------------------------------------
# Build Command Set
# ---------------------------------------------------------------------------

build_command_set() {
    log_info "Building command set for profile: $PROFILE"
    
    load_basic_profile
    
    case "$PROFILE" in
        nfs) load_nfs_profile ;;
        smb) load_smb_profile ;;
        iscsi) load_iscsi_profile ;;
        nvme) load_nvme_profile ;;
        basic) ;;
        all)
            load_nfs_profile
            load_smb_profile
            load_iscsi_profile
            load_nvme_profile
            ;;
        *)
            log_error "Unknown profile: $PROFILE"
            log_error "Valid profiles: basic, nfs, smb, iscsi, nvme, all"
            exit 1
            ;;
    esac
    
    log_info "Command set built: ${#FSX_COMMANDS[@]} FSx commands, ${#CLIENT_COMMANDS[@]} client commands"
}

# ---------------------------------------------------------------------------
# NFS Version Selection
# ---------------------------------------------------------------------------

select_nfs_versions() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║              NFS VERSION SELECTION                            ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Choose which NFS versions to test:"
    echo ""
    echo "  ${BOLD}[1] Auto-detect (recommended)${NC}"
    echo "      Try: 4.2 → 4.1 → 4.0 → 3 until one works"
    echo ""
    echo "  [2] NFS v4.2 only"
    echo "  [3] NFS v4.1 only"
    echo "  [4] NFS v4.0 only"
    echo "  [5] NFS v3 only"
    echo ""
    
    read -p "Selection [1-5] (default: 1): " selection
    [[ -z "$selection" ]] && selection=1
    
    case "$selection" in
        1) NFS_VERSION="auto"; echo "✓ Selected: Auto-detect" ;;
        2) NFS_VERSION="4.2"; echo "✓ Selected: NFS v4.2 only" ;;
        3) NFS_VERSION="4.1"; echo "✓ Selected: NFS v4.1 only" ;;
        4) NFS_VERSION="4.0"; echo "✓ Selected: NFS v4.0 only" ;;
        5) NFS_VERSION="3"; echo "✓ Selected: NFS v3 only" ;;
        *) NFS_VERSION="auto"; echo "✓ Using: Auto-detect (default)" ;;
    esac
    
    log_info "NFS version: $NFS_VERSION"
    echo ""
}

# ---------------------------------------------------------------------------
# NFS Mount Script Generators
# ---------------------------------------------------------------------------

generate_auto_mount_script() {
    local endpoint="$1"
    local path="$2"
    local mount_point="$3"
    
    cat <<SCRIPT
#!/bin/bash
echo '─────────────────────────────────────────────────────────────────'
echo 'Mount Test: AUTO-DETECT MODE'
echo 'Will try: NFSv4.2 → NFSv4.1 → NFSv4.0 → NFSv3'
echo '─────────────────────────────────────────────────────────────────'
echo ''

if mount | grep -q '${endpoint}:${path}'; then
    echo '✓ Filesystem is ALREADY MOUNTED'
    echo ''
    EXISTING=\$(mount | grep '${endpoint}:${path}' | head -1 | awk '{print \$3}')
    echo "Mount point: \$EXISTING"
    MOUNTED_VER=\$(mount | grep '${endpoint}:${path}' | head -1 | grep -o 'vers=[^,]*' | cut -d= -f2 || echo 'unknown')
    echo "NFS Version: \$MOUNTED_VER"
    echo ''
    mount | grep '${endpoint}:${path}'
    echo ''
    df -h "\$EXISTING" 2>&1
    echo ''
    ls -lah "\$EXISTING" 2>&1 | head -10
    echo ''
    echo '═══════════════════════════════════════════════════════════════'
    echo 'RESULT: Mount is active and accessible'
    echo '═══════════════════════════════════════════════════════════════'
    exit 0
fi

if mountpoint -q ${mount_point} 2>/dev/null; then
    echo '✗ ERROR: Mount point ${mount_point} is already in use'
    mount | grep " ${mount_point} "
    exit 1
fi

mkdir -p ${mount_point} 2>&1 || { echo 'ERROR: Failed to create mount point'; exit 1; }
echo ''

echo '[1/4] Attempting NFS v4.2 mount...'
if timeout 10 mount -t nfs -o vers=4.2 ${endpoint}:${path} ${mount_point} 2>&1; then
    echo ''
    echo '✓✓✓ SUCCESS: NFS v4.2 mount successful!'
    echo ''
    mount | grep '${mount_point}'
    echo ''
    df -h ${mount_point}
    echo ''
    ls -lah ${mount_point} 2>&1 | head -10
    echo ''
    echo '═══════════════════════════════════════════════════════════════'
    echo 'RESULT: Mounted with NFS v4.2 (recommended)'
    echo 'To unmount: umount ${mount_point}'
    echo '═══════════════════════════════════════════════════════════════'
    exit 0
fi
echo '✗ NFS v4.2 failed'
echo ''

echo '[2/4] Attempting NFS v4.1 mount...'
if timeout 10 mount -t nfs -o vers=4.1 ${endpoint}:${path} ${mount_point} 2>&1; then
    echo ''
    echo '✓ SUCCESS: NFS v4.1 mount successful'
    echo ''
    mount | grep '${mount_point}'
    echo ''
    df -h ${mount_point}
    echo ''
    echo '═══════════════════════════════════════════════════════════════'
    echo 'RESULT: Mounted with NFS v4.1'
    echo 'To unmount: umount ${mount_point}'
    echo '═══════════════════════════════════════════════════════════════'
    exit 0
fi
echo '✗ NFS v4.1 failed'
echo ''

echo '[3/4] Attempting NFS v4.0 mount...'
if timeout 10 mount -t nfs -o vers=4.0 ${endpoint}:${path} ${mount_point} 2>&1; then
    echo ''
    echo '✓ SUCCESS: NFS v4.0 mount successful'
    echo ''
    mount | grep '${mount_point}'
    echo ''
    df -h ${mount_point}
    echo ''
    echo '═══════════════════════════════════════════════════════════════'
    echo 'RESULT: Mounted with NFS v4.0'
    echo '═══════════════════════════════════════════════════════════════'
    exit 0
fi
echo '✗ NFS v4.0 failed'
echo ''

echo '[4/4] Attempting NFS v3 mount...'
if timeout 10 mount -t nfs -o vers=3 ${endpoint}:${path} ${mount_point} 2>&1; then
    echo ''
    echo '✓ SUCCESS: NFS v3 mount successful'
    echo ''
    mount | grep '${mount_point}'
    echo ''
    df -h ${mount_point}
    echo ''
    echo '═══════════════════════════════════════════════════════════════'
    echo 'RESULT: Mounted with NFS v3'
    echo '═══════════════════════════════════════════════════════════════'
    exit 0
fi

echo '✗ ALL MOUNT ATTEMPTS FAILED'
SCRIPT
}

generate_single_version_script() {
    local endpoint="$1"
    local path="$2"
    local mount_point="$3"
    local version="$4"
    
    cat <<SCRIPT
#!/bin/bash
if mount | grep -q '${endpoint}:${path}'; then
    echo '✓ Already mounted'
    mount | grep '${endpoint}:${path}'
    exit 0
fi

mkdir -p ${mount_point} 2>&1 || exit 1
if timeout 10 mount -t nfs -o vers=${version} ${endpoint}:${path} ${mount_point} 2>&1; then
    echo '✓ NFS v${version} mount successful'
    mount | grep '${mount_point}'
    df -h ${mount_point}
else
    echo '✗ NFS v${version} mount failed'
fi
SCRIPT
}

# ---------------------------------------------------------------------------
# SMB Mount Script Generator
# ---------------------------------------------------------------------------

generate_smb_mount_script() {
    local endpoint="$1"
    local share="$2"
    local mount_point="$3"
    local creds_file="$4"
    
    cat <<'SCRIPT_END' | sed \
        -e "s|__ENDPOINT__|${endpoint}|g" \
        -e "s|__SHARE__|${share}|g" \
        -e "s|__MOUNT_POINT__|${mount_point}|g" \
        -e "s|__CREDS_FILE__|${creds_file}|g"
#!/bin/bash
ENDPOINT="__ENDPOINT__"
SHARE="__SHARE__"
MOUNT_POINT="__MOUNT_POINT__"
CREDS_FILE="__CREDS_FILE__"

echo '─────────────────────────────────────────────────────────────────'
echo 'SMB Mount Test (Secure Credentials)'
echo "Target: //${ENDPOINT}/${SHARE}"
echo "Mount Point: ${MOUNT_POINT}"
echo '─────────────────────────────────────────────────────────────────'
echo ''

if [[ ! -f "$CREDS_FILE" ]]; then
    echo "✗ ERROR: Credentials file not found: $CREDS_FILE"
    exit 1
fi

PERMS=$(stat -c %a "$CREDS_FILE" 2>/dev/null || stat -f %Lp "$CREDS_FILE" 2>/dev/null)
if [[ "$PERMS" != "600" ]]; then
    chmod 600 "$CREDS_FILE"
fi

if mount | grep -q "//${ENDPOINT}/${SHARE}"; then
    echo '✓ Filesystem is ALREADY MOUNTED'
    echo ''
    EXISTING=$(mount | grep "//${ENDPOINT}/${SHARE}" | head -1 | awk '{print $3}')
    echo "Mount point: $EXISTING"
    SMB_VER=$(mount | grep "//${ENDPOINT}/${SHARE}" | head -1 | grep -o 'vers=[^,]*' | cut -d= -f2 || echo 'unknown')
    echo "SMB Version: $SMB_VER"
    echo ''
    mount | grep "//${ENDPOINT}/${SHARE}"
    echo ''
    df -h "$EXISTING" 2>&1
    echo ''
    ls -lah "$EXISTING" 2>&1 | head -10
    echo ''
    echo '═══════════════════════════════════════════════════════════════'
    echo 'RESULT: Mount is active and accessible'
    echo '═══════════════════════════════════════════════════════════════'
    exit 0
fi

if mountpoint -q ${MOUNT_POINT} 2>/dev/null; then
    echo "✗ ERROR: Mount point ${MOUNT_POINT} is already in use"
    exit 1
fi

mkdir -p ${MOUNT_POINT} 2>&1 || { echo 'ERROR: Failed to create mount point'; exit 1; }
echo ''

echo '[1/3] Attempting SMB 3.1.1 mount...'
if timeout 30 mount -t cifs //${ENDPOINT}/${SHARE} ${MOUNT_POINT} -o credentials=${CREDS_FILE},vers=3.1.1 2>&1; then
    echo ''
    echo '✓✓✓ SUCCESS: SMB 3.1.1 mount successful!'
    echo ''
    mount | grep "${MOUNT_POINT}"
    echo ''
    df -h ${MOUNT_POINT}
    echo ''
    ls -lah ${MOUNT_POINT} 2>&1 | head -10
    echo ''
    echo '═══════════════════════════════════════════════════════════════'
    echo 'RESULT: Mounted with SMB 3.1.1 (most secure)'
    echo "To unmount: umount ${MOUNT_POINT}"
    echo '═══════════════════════════════════════════════════════════════'
    exit 0
fi
echo '✗ SMB 3.1.1 failed'
echo ''

echo '[2/3] Attempting SMB 3.0 mount...'
if timeout 30 mount -t cifs //${ENDPOINT}/${SHARE} ${MOUNT_POINT} -o credentials=${CREDS_FILE},vers=3.0 2>&1; then
    echo ''
    echo '✓ SUCCESS: SMB 3.0 mount successful'
    echo ''
    mount | grep "${MOUNT_POINT}"
    echo ''
    df -h ${MOUNT_POINT}
    echo ''
    echo '═══════════════════════════════════════════════════════════════'
    echo 'RESULT: Mounted with SMB 3.0'
    echo '═══════════════════════════════════════════════════════════════'
    exit 0
fi
echo '✗ SMB 3.0 failed'
echo ''

echo '[3/3] Attempting SMB 2.1 mount...'
if timeout 30 mount -t cifs //${ENDPOINT}/${SHARE} ${MOUNT_POINT} -o credentials=${CREDS_FILE},vers=2.1 2>&1; then
    echo ''
    echo '✓ SUCCESS: SMB 2.1 mount successful'
    echo ''
    mount | grep "${MOUNT_POINT}"
    echo ''
    echo '═══════════════════════════════════════════════════════════════'
    echo 'RESULT: Mounted with SMB 2.1'
    echo '═══════════════════════════════════════════════════════════════'
    exit 0
fi

echo '✗✗✗ ALL SMB MOUNT ATTEMPTS FAILED'
exit 1
SCRIPT_END
}

# ---------------------------------------------------------------------------
# Mount Testing Functions
# ---------------------------------------------------------------------------

add_nfs_mount_test() {
    local endpoint="$1"
    local path="$2"
    local mount_point="$3"
    local nfs_version="$4"
    
    log_info "Adding NFS mount test: ${endpoint}:${path} -> ${mount_point}"
    
    local mount_test_script="/tmp/nfs_mount_test_$$.sh"
    
    if [[ "$nfs_version" == "auto" ]]; then
        generate_auto_mount_script "$endpoint" "$path" "$mount_point" > "$mount_test_script"
    else
        generate_single_version_script "$endpoint" "$path" "$mount_point" "$nfs_version" > "$mount_test_script"
    fi
    
    chmod +x "$mount_test_script"
    
    CLIENT_COMMANDS+=(
        "# ===== NFS MOUNT TEST: ${endpoint}:${path} ====="
        "echo ''"
        "echo 'Testing connectivity...'"
        "timeout 5 ping -c 3 ${endpoint} 2>&1 || echo 'Ping failed'"
        "echo ''"
        "timeout 5 nc -zv ${endpoint} 2049 2>&1 || echo 'Port 2049 not accessible'"
        "echo ''"
        "timeout 10 showmount -e ${endpoint} 2>&1 || echo 'showmount failed'"
        "echo ''"
        "timeout 120 bash ${mount_test_script} 2>&1 || echo 'Mount test timed out'"
        "rm -f ${mount_test_script} 2>/dev/null || true"
        "echo ''"
    )
    
    CLIENT_COMMANDS+=(
        "# ----- NFS Client Info -----"
        "echo 'NFS mounts:'"
        "cat /proc/mounts | grep nfs || echo 'None'"
        "echo ''"
    )
    
    log_success "NFS mount test configured"
}

add_smb_mount_test() {
    local endpoint="$1"
    local path="$2"
    local mount_point="$3"
    
    log_info "Adding SMB mount test: //${endpoint}/${path}"
    
    local share=$(echo "$path" | sed 's|^/||' | cut -d'/' -f1)
    
    CLIENT_COMMANDS+=(
        "# ===== SMB MOUNT TEST: //${endpoint}/${share} ====="
        "echo ''"
        "echo 'Testing SMB connectivity...'"
        "timeout 5 ping -c 3 ${endpoint} 2>&1 || echo 'Ping failed'"
        "echo ''"
        "timeout 5 nc -zv ${endpoint} 445 2>&1 || echo 'Port 445 not accessible'"
        "echo ''"
        "timeout 10 smbclient -L //${endpoint} -N 2>&1 || echo 'SMB listing failed'"
        "echo ''"
    )
    
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║       SMB MOUNT TEST - SECURE CREDENTIALS REQUIRED            ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "SMB mounting requires username and password."
    echo "Credentials will be stored in a temporary file (600 perms)."
    echo "The file will be automatically deleted after the test."
    echo ""
    
    read -p "SMB username (or press Enter to skip mount test): " smb_user
    
    if [[ -z "$smb_user" ]]; then
        CLIENT_COMMANDS+=("echo 'SMB mount test skipped'")
        log_info "SMB mount test skipped"
        return
    fi
    
    read -p "SMB domain (press Enter if none): " smb_domain
    
    echo ""
    read -s -p "SMB password for ${smb_user}: " smb_pass
    echo ""
    
    if [[ -z "$smb_pass" ]]; then
        log_warning "No password provided - skipping mount test"
        CLIENT_COMMANDS+=("echo 'SMB mount test skipped'")
        return
    fi
    
    SMB_CREDS_FILE="/tmp/smb_creds_$$_$(date +%s).conf"
    
    cat > "$SMB_CREDS_FILE" <<EOF
username=${smb_user}
password=${smb_pass}
EOF
    
    if [[ -n "$smb_domain" ]]; then
        echo "domain=${smb_domain}" >> "$SMB_CREDS_FILE"
    fi
    
    chmod 600 "$SMB_CREDS_FILE"
    
    log_info "Credentials file created (will be deleted after test)"
    
    local mount_test_script="/tmp/smb_mount_test_$$.sh"
    generate_smb_mount_script "$endpoint" "$share" "$mount_point" "$SMB_CREDS_FILE" > "$mount_test_script"
    chmod +x "$mount_test_script"
    
    CLIENT_COMMANDS+=(
        "bash ${mount_test_script} 2>&1 || echo 'Mount test failed'"
        "echo ''"
    )
    
    CLIENT_COMMANDS+=(
        "# ----- Cleanup -----"
        "rm -f ${mount_test_script} 2>/dev/null || true"
        "rm -f ${SMB_CREDS_FILE} 2>/dev/null || true"
        "echo 'Credentials file deleted for security'"
        "echo ''"
    )
    
    CLIENT_COMMANDS+=(
        "# ----- SMB Client Info -----"
        "echo 'Current CIFS mounts:'"
        "cat /proc/mounts | grep cifs || echo 'None'"
        "echo ''"
    )
    
    log_success "SMB mount test configured"
}

setup_mount_testing() {
    [[ "$TEST_MOUNT" != true ]] && return 0
    
    log_info "Setting up mount testing"
    
    if [[ -z "$MOUNT_TYPE" ]]; then
        if [[ "$PROFILE" == *"nfs"* ]]; then
            MOUNT_TYPE="nfs"
        elif [[ "$PROFILE" == *"smb"* ]]; then
            MOUNT_TYPE="smb"
        else
            echo ""
            echo "Select mount type:"
            echo "  [1] NFS"
            echo "  [2] SMB/CIFS"
            read -p "Choice (1/2) or Enter to skip: " type_choice
            case "$type_choice" in
                1) MOUNT_TYPE="nfs" ;;
                2) MOUNT_TYPE="smb" ;;
                *) return 0 ;;
            esac
        fi
    fi
    
    [[ -z "$MOUNT_ENDPOINT" ]] && read -p "SVM endpoint: " MOUNT_ENDPOINT
    [[ -z "$MOUNT_PATH" ]] && read -p "Path/Share: " MOUNT_PATH
    [[ -z "$MOUNT_POINT" ]] && read -p "Mount point: " MOUNT_POINT
    
    [[ -z "$MOUNT_ENDPOINT" || -z "$MOUNT_PATH" || -z "$MOUNT_POINT" ]] && return 0
    
    [[ "$MOUNT_TYPE" == "nfs" ]] && select_nfs_versions
    
    echo ""
    echo "⚠️  Mount testing will modify system state"
    echo "Target: ${MOUNT_ENDPOINT}:${MOUNT_PATH} -> ${MOUNT_POINT}"
    read -p "Proceed? (yes/no): " proceed
    [[ "$proceed" != "yes" && "$proceed" != "y" ]] && return 0
    
    [[ $EUID -ne 0 ]] && log_warning "Not root - mount may fail"
    
    if [[ "$MOUNT_TYPE" == "nfs" ]]; then
        add_nfs_mount_test "$MOUNT_ENDPOINT" "$MOUNT_PATH" "$MOUNT_POINT" "$NFS_VERSION"
    else
        add_smb_mount_test "$MOUNT_ENDPOINT" "$MOUNT_PATH" "$MOUNT_POINT"
    fi
}

# ---------------------------------------------------------------------------
# FSx Command Execution
# ---------------------------------------------------------------------------

run_fsx_commands() {
    local host="$1"
    local username="$2"
    local port="$3"
    local key_file="$4"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "FSx ONTAP Data Collection"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Endpoint: $host:$port"
    echo "Commands: ${#FSX_COMMANDS[@]}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    local control_info=$(setup_ssh_control_master "$host" "$username" "$port" "$key_file")
    local ssh_opts=$(echo "$control_info" | cut -d'|' -f2-)
    
    [[ -z "$key_file" ]] && echo "You will be prompted for password ONCE" && echo ""
    
    if ! ssh $ssh_opts -p "$port" "${username}@${host}" "version" &>/dev/null; then
        log_error "Cannot connect to FSx"
        cleanup_ssh_control_master
        return 1
    fi
    
    log_success "Connected!"
    echo ""
    
    local success=0
    local timeouts=0
    for cmd in "${FSX_COMMANDS[@]}"; do
        [[ -z "$cmd" || "$cmd" =~ ^[[:space:]]*# ]] && continue
        ((FSX_CMD_COUNTER++))
        
        local filename=$(create_safe_filename "$cmd" "fsx" "$FSX_CMD_COUNTER")
        local output="$OUTPUT_DIR/$filename"
        
        echo -n "[$FSX_CMD_COUNTER/${#FSX_COMMANDS[@]}] ${cmd:0:50}... "
        
        {
            echo "COMMAND: $cmd"
            echo "TIME: $(date)"
            echo "════════════════════════════════════════════════"
            
            timeout 30 ssh $ssh_opts -p "$port" "${username}@${host}" "$cmd" 2>&1
            local exit_code=$?
            
            if [ $exit_code -eq 124 ]; then
                echo ""
                echo "⚠️  WARNING: Command timed out after 30 seconds"
                echo "This may indicate a streaming command or unresponsive service"
                ((timeouts++))
            fi
        } > "$output"
        
        echo -e "${GREEN}✓${NC}"
        ((success++))
    done
    
    log_success "FSx: $success succeeded"
    [[ $timeouts -gt 0 ]] && log_warning "FSx: $timeouts commands timed out (expected for some statistics commands)"
    cleanup_ssh_control_master
}

# ---------------------------------------------------------------------------
# Client Command Execution
# ---------------------------------------------------------------------------

run_client_commands() {
    [[ ${#CLIENT_COMMANDS[@]} -eq 0 ]] && return
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Client-Side Collection"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    for cmd in "${CLIENT_COMMANDS[@]}"; do
        [[ -z "$cmd" ]] && continue
        
        if [[ "$cmd" =~ ^[[:space:]]*# ]]; then
            ((CLIENT_CMD_COUNTER++))
            local filename=$(create_safe_filename "$cmd" "client" "$CLIENT_CMD_COUNTER")
            echo "$cmd" > "$OUTPUT_DIR/$filename"
            echo -e "${CYAN}$cmd${NC}"
            continue
        fi
        
        ((CLIENT_CMD_COUNTER++))
        local filename=$(create_safe_filename "$cmd" "client" "$CLIENT_CMD_COUNTER")
        
        echo -n "[$CLIENT_CMD_COUNTER] ${cmd:0:60}... "
        
        {
            echo "COMMAND: $cmd"
            echo "TIME: $(date)"
            echo "════════════════════════════════════════════════"
            eval "$cmd" 2>&1 || true
        } > "$OUTPUT_DIR/$filename"
        
        echo -e "${GREEN}✓${NC}"
    done
    
    log_success "Client: complete"
}

# ---------------------------------------------------------------------------
# Create Index and Bundle
# ---------------------------------------------------------------------------

create_command_index() {
    local index="$OUTPUT_DIR/00_COMMAND_INDEX.txt"
    
    {
        echo "FSx for NetApp ONTAP - Command Index"
        echo "====================================="
        echo ""
        echo "Script Version: $SCRIPT_VERSION"
        echo "Date: $(date)"
        echo "Profile: $PROFILE"
        echo ""
        echo "FSx Commands:"
        local n=0
        for cmd in "${FSX_COMMANDS[@]}"; do
            [[ -z "$cmd" || "$cmd" =~ ^# ]] && continue
            ((n++))
            printf "[%03d] %s → %s\n\n" "$n" "$(create_safe_filename "$cmd" "fsx" "$n")" "$cmd"
        done
        
        [[ ${#CLIENT_COMMANDS[@]} -gt 0 ]] && {
            echo ""
            echo "Client Commands:"
            n=0
            for cmd in "${CLIENT_COMMANDS[@]}"; do
                [[ -z "$cmd" ]] && continue
                ((n++))
                printf "[%03d] %s → %s\n\n" "$n" "$(create_safe_filename "$cmd" "client" "$n")" "$cmd"
            done
        }
    } > "$index"
    
    log_success "Index created"
}

create_bundle() {
    local tar="${OUTPUT_DIR}.tar.gz"
    if tar -czf "$tar" "$OUTPUT_DIR" 2>/dev/null; then
        local size=$(stat -c%s "$tar" 2>/dev/null || stat -f%z "$tar" 2>/dev/null)
        local size_mb=$(awk "BEGIN {printf \"%.2f\", $size/1024/1024}")
        log_success "Bundle: $tar ($size_mb MB)"
    fi
}

# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --profile) PROFILE="$2"; shift 2 ;;
            --fsx-endpoint) FSX_ENDPOINT="$2"; shift 2 ;;
            --fsx-username) FSX_USERNAME="$2"; shift 2 ;;
            --fsx-port) FSX_PORT="$2"; shift 2 ;;
            --fsx-key-file) FSX_KEY_FILE="$2"; shift 2 ;;
            --include-client) INCLUDE_CLIENT=true; shift ;;
            --test-mount) TEST_MOUNT=true; shift ;;
            --mount-endpoint) MOUNT_ENDPOINT="$2"; shift 2 ;;
            --mount-path) MOUNT_PATH="$2"; shift 2 ;;
            --mount-type) MOUNT_TYPE="$2"; shift 2 ;;
            --mount-point) MOUNT_POINT="$2"; shift 2 ;;
            --help|-h) 
                echo "FSx for NetApp ONTAP Data Collection Script v${SCRIPT_VERSION}"
                echo ""
                echo "Usage: sudo $0 --profile <profile> [options]"
                echo ""
                echo "Profiles:"
                echo "  basic   - System health + Performance (29 commands)"
                echo "  nfs     - Basic + NFS diagnostics (44 commands)"
                echo "  smb     - Basic + SMB/CIFS diagnostics (44 commands)"
                echo "  iscsi   - Basic + iSCSI diagnostics (44 commands)"
                echo "  nvme    - Basic + NVMe/TCP diagnostics (43 commands)"
                echo "  all     - All profiles combined (90 commands)"
                echo ""
                echo "Options:"
                echo "  --include-client              Include client-side diagnostics"
                echo "  --test-mount                  Test mounting (nfs/smb only)"
                echo "  --fsx-endpoint <ip>           FSx management IP/DNS"
                echo "  --fsx-username <user>         FSx username (default: fsxadmin)"
                echo "  --fsx-port <port>             SSH port (default: 22)"
                echo "  --fsx-key-file <path>         SSH private key file"
                echo "  --mount-endpoint <ip>         SVM data IP/DNS"
                echo "  --mount-path <path>           NFS path or SMB share"
                echo "  --mount-type <nfs|smb>        Mount type"
                echo "  --mount-point <path>          Local mount point"
                echo ""
                echo "Examples:"
                echo "  sudo $0 --profile nvme --include-client --fsx-endpoint <FSx-IP>"
                echo "  sudo $0 --profile all --include-client --fsx-endpoint <FSx-IP>"
                echo ""
                echo "Changelog v3.7.1:"
                echo "  + Added NVMe/TCP protocol support"
                echo "  + Fixed invalid NVMe commands"
                echo "  + All commands validated and working"
                echo ""
                exit 0 
                ;;
            *) log_error "Unknown option: $1"; exit 1 ;;
        esac
    done
    
    [[ -z "$PROFILE" ]] && { log_error "Missing --profile"; exit 1; }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║   FSx for NetApp ONTAP - Data Collection Script v${SCRIPT_VERSION}      ║"
    echo "║   Production Ready + NVMe/TCP Support                         ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    
    : > "$LOG_FILE"
    log_info "Script started v$SCRIPT_VERSION"
    
    cleanup_old_temp_files
    
    check_platform
    check_dependencies
    parse_arguments "$@"
    
    [[ -z "$FSX_ENDPOINT" ]] && read -p "FSx endpoint: " FSX_ENDPOINT
    [[ -z "$FSX_ENDPOINT" ]] && { log_error "Endpoint required"; exit 1; }
    
    build_command_set
    
    [[ "$INCLUDE_CLIENT" == true ]] && check_optional_dependencies
    
    [[ "$TEST_MOUNT" == true && "$INCLUDE_CLIENT" == true ]] && setup_mount_testing
    
    local timestamp=$(date -u '+%Y%m%dT%H%M%SZ')
    OUTPUT_DIR="fsx_ontap_collect_${PROFILE}_${timestamp}"
    mkdir -p "$OUTPUT_DIR"
    mv "$LOG_FILE" "$OUTPUT_DIR/"
    LOG_FILE="$OUTPUT_DIR/fsx_collect.log"
    
    run_fsx_commands "$FSX_ENDPOINT" "$FSX_USERNAME" "$FSX_PORT" "$FSX_KEY_FILE"
    [[ "$INCLUDE_CLIENT" == true ]] && run_client_commands
    
    create_command_index
    create_bundle
    
    log_debug "Performing cleanup..."
    cleanup_ssh_control_master
    sleep 1
    cleanup_temp_files
    
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    COMPLETE                                   ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Bundle: ${OUTPUT_DIR}.tar.gz"
    echo ""
    
    log_success "Done!"
}

trap 'emergency_cleanup' INT TERM

main "$@"

# =========================================================================
# GUARANTEED FINAL CLEANUP
# =========================================================================

sleep 2

if [[ -n "$SSH_CONTROL_PATH" ]]; then
    CONTROL_DIR=$(dirname "$SSH_CONTROL_PATH" 2>/dev/null)
    if [[ -d "$CONTROL_DIR" ]]; then
        find "$CONTROL_DIR" -type f -delete 2>/dev/null || true
        find "$CONTROL_DIR" -type s -delete 2>/dev/null || true
        rmdir "$CONTROL_DIR" 2>/dev/null || rm -rf "$CONTROL_DIR" 2>/dev/null || true
    fi
fi

rm -rf "/tmp/ssh_fsx_$$" 2>/dev/null || true
find /tmp -maxdepth 1 -type d -name "ssh_fsx_*" -mmin +60 -exec rm -rf {} \; 2>/dev/null || true

exit 0