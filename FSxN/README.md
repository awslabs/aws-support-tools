# FSx for NetApp ONTAP - Diagnostic Data Collection Tool
 
**Author:** Sofien Abid (AWS Support)  
**Platform:** Linux only

A diagnostic tool for collecting configuration and troubleshooting data from AWS FSx for NetApp ONTAP file systems and Linux clients.

---

## License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License").
You may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

---

## Overview

This script automates the collection of diagnostic data from FSx for NetApp ONTAP file systems and Linux clients. It is designed to help AWS Support Engineers and customers quickly gather comprehensive system information for troubleshooting purposes.

The script connects to your FSx file system via SSH and executes a series of NetApp ONTAP commands, while optionally collecting client-side diagnostic information from the Linux system where it runs.

---

## When To Use This

**General health check**
→ Use `basic` profile

**NFS mount issues**
→ Use `nfs --include-client`

**SMB/CIFS issues**
→ Use `smb --include-client`

**iSCSI connectivity**
→ Use `iscsi --include-client`

**NVMe/TCP issues**
→ Use `nvme --include-client`

**Unknown or complex issue**
→ Use `all --include-client`

---

## Quick Start

```bash
# Download/Copy the script in a file example "fsx_collect.sh"
chmod +x fsx_collect.sh

# Basic collection (FSx health check only)
sudo ./fsx_collect.sh --profile basic --fsx-endpoint <mgmt-ip>

# NFS troubleshooting with client data
sudo ./fsx_collect.sh --profile nfs --include-client --fsx-endpoint <mgmt-ip>

# SMB/CIFS troubleshooting with client data
sudo ./fsx_collect.sh --profile smb --include-client --fsx-endpoint <mgmt-ip>

# iSCSI troubleshooting with client data
sudo ./fsx_collect.sh --profile iscsi --include-client --fsx-endpoint <mgmt-ip>

# NVMe/TCP troubleshooting with client data
sudo ./fsx_collect.sh --profile nvme --include-client --fsx-endpoint <mgmt-ip>

# Comprehensive (all protocols)
sudo ./fsx_collect.sh --profile all --include-client --fsx-endpoint <mgmt-ip>
Profiles

## Profiles

The script supports six profiles for targeted data collection:

**basic**
→ 29 FSx commands, 0 client commands
→ System health and performance only

**nfs**
→ 44 FSx commands, 22 client commands
→ Basic + NFS-specific diagnostics

**smb**
→ 44 FSx commands, 22 client commands
→ Basic + SMB/CIFS-specific diagnostics

**iscsi**
→ 44 FSx commands, 21 client commands
→ Basic + iSCSI/SAN-specific diagnostics

**nvme**
→ 40 FSx commands, 19 client commands
→ Basic + NVMe/TCP-specific diagnostics

**all**
→ 90 FSx commands, 80+ client commands
→ All profiles combined

What It Collects

FSx Side (via SSH)

Cluster/node health
Network interfaces & routing
Volume/aggregate info
Export policies (NFS)
CIFS shares & sessions (SMB)
LUN mappings (iSCSI)
NVMe subsystems
QoS policies
Event logs
Client Side (local)

OS/kernel info
Current mounts & fstab
Network config
Protocol-specific stats (nfsstat, iscsiadm, etc.)
Relevant dmesg/journalctl logs
Command-Line Options

Required

--profile <profile>          Profile to use: basic, nfs, smb, iscsi, nvme, or all
--fsx-endpoint <address>     FSx management endpoint (IP address or DNS name)
FSx Connection

--fsx-username <user>        FSx username (default: fsxadmin)
--fsx-port <port>            SSH port (default: 22)
--fsx-key-file <path>        Path to SSH private key file (optional)
Client-Side Collection

--include-client             Collect client-side diagnostics
Mount Testing

--test-mount                 Test NFS or SMB mounting (requires --include-client)
--mount-endpoint <address>   SVM data endpoint (NFS/SMB/iSCSI LIF IP or DNS)
--mount-path <path>          NFS export path or SMB share name
--mount-type <nfs|smb>       Type of mount to test
--mount-point <path>         Local directory to use as mount point
Help

--help, -h                   Display help message and exit
Security Notes

FSx password → Prompted via terminal (not echoed), stored only in memory

SMB credentials → Temp file with 600 perms, securely deleted after use

SSH connection → Uses ControlMaster, cleaned up on exit

Output bundle → Contains config only, NOT file contents from volumes

Output Bundle Contents

fsx_ontap_collect_<profile>_<timestamp>.tar.gz
└── fsx_ontap_collect_<profile>_<timestamp>/
    ├── 00_COMMAND_INDEX.txt    # Maps filenames to commands
    ├── fsx_collect.log         # Execution log
    ├── fsx_001_version.txt     # FSx command outputs
    ├── fsx_002_cluster_show.txt
    ├── ...
    ├── client_001_uname_a.txt  # Client outputs (if --include-client)
    └── ...
Alternative Manual Commands

If customer cannot run the script, here are the key commands to request:

FSx Side (SSH to management endpoint as fsxadmin)

Basic Health:

version
cluster show
system health status show
system health alert show
event log show -severity error -time >7d
Network:

network interface show
network route show
vserver show
Storage:

volume show -fields volume,vserver,state,size,available,percent-used,junction-path
storage aggregate show
df -h
NFS Specific:

vserver nfs show
vserver nfs show -fields v3,v4.0,v4.1,v4.2
export-policy rule show -fields policy,ruleindex,clientmatch,rorule,rwrule,superuser
vserver nfs connected-clients show
SMB Specific:

vserver cifs show
vserver cifs check
vserver cifs share show
vserver cifs session show
iSCSI Specific:

vserver iscsi show
lun show -fields path,size,state,mapped
lun mapping show
lun igroup show
NVMe Specific:

vserver nvme show
vserver nvme subsystem show
vserver nvme namespace show
Client Side (Linux)

General:

uname -a
cat /etc/os-release
mount | grep -E 'nfs|cifs'
cat /etc/fstab | grep -E 'nfs|cifs'
ip addr
ip route

NFS:

nfsstat -m
nfsstat -c
showmount -e <svm-ip>
cat /proc/mounts | grep nfs
dmesg | grep -i nfs | tail -50

SMB:

mount | grep cifs
cat /proc/fs/cifs/DebugData
dmesg | grep -i cifs | tail -50

iSCSI:

iscsiadm -m session -P 3
cat /etc/iscsi/initiatorname.iscsi
multipath -ll
lsblk

Troubleshooting

SSH connection fails → Check security group allows port 22 from client to FSx mgmt endpoint

Mount test fails → Verify using DATA endpoint (SVM LIF), not management endpoint

Permission denied → Run with sudo

Missing tools warning → Non-critical - script continues with available tools

Version History

v3.7.1 - January 2026

Added NVMe/TCP support
Fixed invalid commands
All commands validated and working
Support

Author: Sofien Abid
Issues: https://github.com/awslabs/aws-support-tools/issues
For issues or feedback, please open an issue in this repository.
