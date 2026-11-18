# Nitro instance type pre-flight checks

Run this script on a Linux instance **before** changing its instance type to a Nitro-based type (for example from `t2`/`m4`/`c4` to `t3`/`m5`/`c5` and later). It checks the four things that most often stop an instance from booting or networking after the change, and can fix two of them for you.

| Check | What it looks at | Can fix |
|---|---|---|
| NVMe driver | Built into the running kernel, or present as a module **and** included in the initramfs for that kernel | No (prints the `dracut` / `update-initramfs` command to run) |
| NVMe I/O timeout | The kernel command line of every installed boot entry (BLS entries, grubenv `kernelopts`, or `grub.cfg`), compared against the maximum the running kernel accepts | Yes |
| ENA driver | Built in or available as a module | No |
| `/etc/fstab` | Entries mounted by `/dev/sd*` or `/dev/xvd*` device name, which change to `/dev/nvme*` on Nitro | Yes (rewrites them as `UUID=`) |

Reference documentation:

- [Amazon EBS volumes and NVMe](https://docs.aws.amazon.com/ebs/latest/userguide/nvme-ebs-volumes.html)
- [NVMe I/O operation timeout for Amazon EBS volumes](https://docs.aws.amazon.com/ebs/latest/userguide/timeout-nvme-ebs-volumes.html)
- [Enhanced networking with ENA](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/enhanced-networking-ena.html)

## Running the script

Copy the script to the instance and run it as root:

```
chmod +x nitro_check_script.sh
sudo ./nitro_check_script.sh          # interactive: prompts before each change
sudo ./nitro_check_script.sh -n       # check only, never modifies anything
sudo ./nitro_check_script.sh -y       # apply all fixes without prompting
```

When standard input is not a terminal (SSM Run Command, cron, `curl | bash`) the script runs in check-only mode automatically, so it will never prompt or modify anything unattended unless you pass `-y`.

Exit status: `0` all checks passed, `2` at least one WARNING or ERROR remains, `1` not run as root or bad option. This makes it usable across a fleet with SSM Run Command.

## What the fixes change

**NVMe I/O timeout.** Adds `nvme_core.io_timeout=4294967295` (or `nvme.io_timeout=255` on kernels older than 4.6) to every installed kernel's boot entry so it takes effect on the next reboot, and persists it so future kernels inherit it. On systems with `grubby` (RHEL, CentOS, Rocky, AlmaLinux, Oracle Linux, Fedora, Amazon Linux) the boot entries are edited in place with `grubby --update-kernel=ALL --args=...`, which is the only method that works on RHEL 9.3 and later where `grub2-mkconfig` no longer rewrites Boot Loader Specification entries. On SLES it edits `/etc/default/grub` and runs `grub2-mkconfig`. On Debian and Ubuntu it runs `update-grub`, and on Ubuntu cloud images it writes the parameter into a `/etc/default/grub.d` drop-in so it reaches the `GRUB_FORCE_PARTUUID` initrdless boot entry. Any file it changes is first copied to `<file>.backup.<timestamp>`.

**fstab.** Each `/dev/sd*` or `/dev/xvd*` entry is resolved through any udev symlink to the real block device, and replaced with that device's filesystem `UUID=`. Entries whose device does not exist or has no filesystem are left unchanged and reported. The original is saved as `/etc/fstab.backup.<timestamp>`.

## Tested on

Amazon Linux 1, Amazon Linux 2 (4.14 and 5.10 kernels), Amazon Linux 2023 (x86_64 and arm64), Ubuntu 18.04, 20.04, 22.04 and 24.04 (x86_64 and arm64), Debian 11 and 12, RHEL 7.9, 8.10, 9.6 and 10.0, Rocky Linux 9, AlmaLinux 9, CentOS Stream 9, Oracle Linux 8 and 9, Fedora, and SLES 15. Xen (`t2`) and Nitro (`t4g`, `t3`) instance types, BIOS and UEFI, hosts with multiple installed kernels, and fstab entries on LVM, LUKS (via crypttab) and mdraid, which are left untouched. Each fix was confirmed by rebooting and checking the running kernel command line and mounts.

## Prerequisites

Root. `lsinitrd` (dracut) or `lsinitramfs` (initramfs-tools) to inspect the initramfs; `blkid` or `lsblk` for the fstab conversion. All are present on the distributions above.
