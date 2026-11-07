#!/bin/bash

########################################################################

# Copyright 2018-2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

########################################################################
#
# Pre-flight checks before changing an EC2 instance to a Nitro-based instance type.
#
#   1. NVMe driver present (built into the kernel, or a module that is in the initramfs)
#   2. NVMe I/O timeout set to the recommended value in the bootloader configuration
#   3. ENA driver present
#   4. /etc/fstab does not mount by /dev/sd* or /dev/xvd* device name
#
# Usage:  sudo ./nitro_check_script.sh [-y | -n] [-h]
#   -y   apply fixes without prompting
#   -n   check only, never modify anything (default when stdin is not a terminal)
#   (no flag, interactive terminal)  prompt before each change, as before
#
# Exit status: 0 = everything OK, 2 = at least one WARNING or ERROR remains, 1 = usage/root error
#
# References:
#   https://docs.aws.amazon.com/ebs/latest/userguide/nvme-ebs-volumes.html
#   https://docs.aws.amazon.com/ebs/latest/userguide/timeout-nvme-ebs-volumes.html
#   https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/enhanced-networking-ena.html
#
########################################################################

PATH=/bin:/sbin:/usr/bin:/usr/sbin
export LC_ALL=C

MODE=ask            # ask | yes | no
ISSUES=0
KVER=$(uname -r)
NVME_UINT_MAX=4294967295
NVME_BYTE_MAX=255

usage () {
    sed -n '/^# Usage:/,/^# Exit status/p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
}

while [ $# -gt 0 ]; do
    case "$1" in
        -y|--yes) MODE=yes ;;
        -n|--no|--check-only) MODE=no ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
    shift
done

if [ "$MODE" = ask ] && [ ! -t 0 ]; then
    # No terminal to answer prompts on (piped, SSM, cron): never modify anything.
    MODE=no
fi

ok ()   { echo -e "\n\nOK       $*"; }
warn () { echo -e "\n\nWARNING  $*"; ISSUES=$((ISSUES+1)); }
err ()  { echo -e "\n\nERROR    $*"; ISSUES=$((ISSUES+1)); }
# fixfail: a fix attempt did not complete. The problem was already counted by the warn that led
# here, so report it without adding to ISSUES a second time.
fixfail () { echo -e "\n\nERROR    $*"; }
note () { echo -e "\t- $*"; }

# confirm "question": 0 means go ahead with the change, 1 means skip it
confirm () {
    case "$MODE" in
        yes) echo "(auto-yes) $1"; return 0 ;;
        no)  echo "(check only, not modifying) $1"; return 1 ;;
    esac
    local RESPONSE
    printf '\n%s (y/n) ' "$1"
    read -r RESPONSE
    case "$RESPONSE" in
        [yY]|[yY][eE][sS]) return 0 ;;
        *) echo "Not saving changes."; return 1 ;;
    esac
}

########################################################################
# Helpers for kernel modules

# module_state NAME: "builtin", "module" or "missing"
module_state () {
    local name=$1 alt=${1//_/-}
    if grep -qE "/(${name}|${alt})\.ko$" "/lib/modules/${KVER}/modules.builtin" 2>/dev/null; then
        echo builtin; return
    fi
    if modinfo -n "$name" >/dev/null 2>&1; then
        case "$(modinfo -n "$name" 2>/dev/null)" in
            "(builtin)") echo builtin ;;
            *) echo module ;;
        esac
        return
    fi
    echo missing
}

# initramfs_file: the running kernel's initramfs path, or nothing if none is found
initramfs_file () {
    local f
    for f in "/boot/initramfs-${KVER}.img" "/boot/initrd.img-${KVER}" "/boot/initrd-${KVER}" "/boot/initramfs-${KVER}"; do
        [ -f "$f" ] && { echo "$f"; return; }
    done
}

# initramfs_has_module FILE NAME: 0 if NAME.ko (any compression) is in the image
initramfs_has_module () {
    local file=$1 name=$2 alt=${2//_/-} listing
    if command -v lsinitrd >/dev/null 2>&1; then
        listing=$(lsinitrd "$file" 2>/dev/null)
    elif command -v lsinitramfs >/dev/null 2>&1; then
        listing=$(lsinitramfs "$file" 2>/dev/null)
    else
        return 2
    fi
    # No module directory in the listing means we could not read the image, not that it is empty.
    # lsinitrd without skipcpio (Amazon Linux 1, #98) lists only the early microcode cpio.
    if [ -z "$listing" ] || ! printf '%s\n' "$listing" | grep -q 'lib/modules/'; then
        return 2
    fi
    printf '%s\n' "$listing" | grep -qE "/(${name}|${alt})\.ko(\.(gz|xz|zst|bz2|lz4))?([[:space:]]|$)"
}

########################################################################

check_nvme_driver () {
    local state initrd
    state=$(module_state nvme)
    case "$state" in
        builtin)
            ok "NVMe driver is built into the running kernel (${KVER})"
            return ;;
        missing)
            err "NVMe driver is not available on your instance."
            note "Install an NVMe-capable kernel before changing your instance type to Nitro. See:"
            note "https://docs.aws.amazon.com/ebs/latest/userguide/nvme-ebs-volumes.html"
            return ;;
    esac

    ok "NVMe kernel module is installed for kernel ${KVER}"
    initrd=$(initramfs_file)
    if [ -z "$initrd" ]; then
        warn "Could not find an initramfs for the running kernel under /boot; unable to confirm the NVMe module is in it."
        return
    fi
    initramfs_has_module "$initrd" nvme
    case $? in
        0) ok "NVMe module is present in ${initrd}" ;;
        2) warn "Unable to list the contents of ${initrd} (lsinitrd/lsinitramfs missing or failed); cannot confirm the NVMe module is in it." ;;
        *)
            err "NVMe module is not in the initramfs image ${initrd}."
            note "The instance will not find its root volume on a Nitro instance type. Rebuild the initramfs:"
            if command -v dracut >/dev/null 2>&1; then
                note "# dracut -f -v"
            elif command -v update-initramfs >/dev/null 2>&1; then
                note "# update-initramfs -u -k all"
            elif command -v mkinitrd >/dev/null 2>&1; then
                note "# mkinitrd"
            else
                note "(use your distribution's initramfs tool)"
            fi ;;
    esac
}

########################################################################
# NVMe io_timeout

# detect_nvme_param: nvme_core on kernels 4.6+ (uint io_timeout), nvme on older ones (byte).
# Sets NVME_PARAM and NVME_MAX to what the running kernel accepts.
detect_nvme_param () {
    local parm
    NVME_PARAM=nvme_core; NVME_MAX=$NVME_UINT_MAX
    parm=$(modinfo nvme_core 2>/dev/null | grep -E '^parm:[[:space:]]+io_timeout:')
    if [ -z "$parm" ]; then
        parm=$(modinfo nvme 2>/dev/null | grep -E '^parm:[[:space:]]+io_timeout:')
        [ -n "$parm" ] && NVME_PARAM=nvme
    fi
    case "$parm" in
        *"(byte)"*) NVME_MAX=$NVME_BYTE_MAX ;;
        *"(uint)"*) NVME_MAX=$NVME_UINT_MAX ;;
        "") # no parm line visible (very old kmod with builtin module); fall back on kernel version
            case "$KVER" in
                2.*|3.*|4.[0-5].*) NVME_PARAM=nvme; NVME_MAX=$NVME_BYTE_MAX ;;
            esac ;;
    esac
}

# bootloader_cmdlines: every kernel command line the bootloader will use, one per line,
# from whatever source this system boots from.
bootloader_cmdlines () {
    local f
    if command -v grubby >/dev/null 2>&1 && grubby --info=ALL >/dev/null 2>&1; then
        # BLS systems (RHEL/CentOS/Rocky/Alma 8+, Fedora, AL2023) and legacy grub (RHEL 6, AL1)
        grubby --info=ALL 2>/dev/null | sed -n 's/^args="\(.*\)"$/\1/p'
        # On RHEL 8 the BLS options are "$kernelopts", resolved from grubenv.
        grub2-editenv - list 2>/dev/null | sed -n 's/^kernelopts=//p'
        return
    fi
    if ls /boot/loader/entries/*.conf >/dev/null 2>&1; then
        grep -h '^options' /boot/loader/entries/*.conf | sed 's/^options[[:space:]]*//'
        grub2-editenv - list 2>/dev/null | sed -n 's/^kernelopts=//p'
        return
    fi
    for f in /boot/grub2/grub.cfg /boot/grub/grub.cfg /boot/efi/EFI/*/grub.cfg /boot/grub/menu.lst /boot/grub/grub.conf; do
        [ -f "$f" ] || continue
        grep -hE '^[[:space:]]*(linux|linuxefi|linux16|kernel)[[:space:]]' "$f" 2>/dev/null
        grep -hE '^[[:space:]]*set[[:space:]]+(default_)?kernelopts=' "$f" 2>/dev/null
    done
}

# grub_default_add_param VAR PARAM: add PARAM inside the quotes of VAR= in /etc/default/grub
grub_default_add_param () {
    local var=$1 param=$2 file=/etc/default/grub
    if grep -qE "^${var}=.*(^|[[:space:]\"'])nvme(_core)?\.io_timeout=[0-9]+" "$file"; then
        # already carries an io_timeout of either name; replace it, do not add a second one
        sed -i -E "/^${var}=/ s/nvme(_core)?\.io_timeout=[0-9]+/${param}/g" "$file"
    elif grep -qE "^${var}=\"[^\"]*\"" "$file"; then
        sed -i -E "s/^(${var}=\")([^\"]*)\"/\1\2 ${param}\"/; /^${var}=/ s/=\" /=\"/" "$file"
    elif grep -qE "^${var}='[^']*'" "$file"; then
        sed -i -E "s/^(${var}=')([^']*)'/\1\2 ${param}'/; /^${var}=/ s/=' /='/" "$file"
    elif grep -qE "^${var}=" "$file"; then
        sed -i -E "s/^${var}=(.*)$/${var}=\"\1 ${param}\"/; /^${var}=/ s/=\" /=\"/" "$file"
    else
        printf '%s="%s"\n' "$var" "$param" >> "$file"
    fi
}

# timeout_coverage: sets TOTAL (boot entries, recovery entries excluded) and WITH (entries that
# already carry io_timeout at the required value). Also sets VALUES to every io_timeout value seen.
timeout_coverage () {
    local lines
    lines=$(bootloader_cmdlines | grep -vE '(^|[[:space:]])(recovery|single)([[:space:]]|$)' | grep -v '^[[:space:]]*$')
    TOTAL=$(printf '%s\n' "$lines" | grep -c .)
    WITH=$(printf '%s\n' "$lines" | grep -cE "nvme(_core)?\.io_timeout=${NVME_MAX}([[:space:]]|$)")
    VALUES=$(printf '%s\n' "$lines" | grep -oE 'nvme(_core)?\.io_timeout=[0-9]+' | cut -d= -f2 | sort -un)
}

check_nvme_timeout () {
    local time_stamp v lowest=0 effective param backup_note
    time_stamp=$(date +%F-%H:%M:%S)
    detect_nvme_param
    param="${NVME_PARAM}.io_timeout=${NVME_MAX}"

    # Value the running kernel is using now, if the driver is loaded or built in
    effective=$(cat /sys/module/nvme_core/parameters/io_timeout 2>/dev/null || cat /sys/module/nvme/parameters/io_timeout 2>/dev/null)

    timeout_coverage
    if [ "$TOTAL" -eq 0 ]; then
        warn "Could not locate a bootloader configuration to inspect for ${NVME_PARAM}.io_timeout."
        [ -n "$effective" ] && note "The running kernel reports io_timeout=${effective}."
        return
    fi

    # Every boot entry must carry the value, not just one of them: an entry without the parameter
    # boots with the 30 second default no matter what the other entries say.
    if [ "$WITH" -eq "$TOTAL" ]; then
        ok "NVMe io_timeout=${NVME_MAX} is set on all ${TOTAL} kernel boot entries"
        [ -n "$effective" ] && [ "$effective" != "$NVME_MAX" ] && note "Running kernel currently reports io_timeout=${effective}; the new value applies after a reboot."
        return
    fi
    if [ -n "$VALUES" ]; then
        lowest=$(printf '%s\n' "$VALUES" | head -1)
        if [ "$lowest" -lt "$NVME_MAX" ] 2>/dev/null; then
            warn "NVMe io_timeout is set to ${lowest} on some boot entries, below the recommended ${NVME_MAX}."
        else
            warn "NVMe io_timeout is set on ${WITH} of ${TOTAL} kernel boot entries; the others boot with the 30 second default."
        fi
    else
        warn "NVMe io_timeout is not set in the bootloader configuration (kernel default is 30 seconds)."
    fi
    note "Set ${param} so that EBS I/O under Nitro is retried instead of failed. See:"
    note "https://docs.aws.amazon.com/ebs/latest/userguide/timeout-nvme-ebs-volumes.html"

    confirm "Add ${param} to the kernel command line of every installed kernel?" || return

    echo -e "\n***********************"
    local USE_GRUBBY=0 gen="" values="$VALUES"
    if command -v grubby >/dev/null 2>&1 && grubby --info=ALL >/dev/null 2>&1; then
        USE_GRUBBY=1
    else
        if command -v update-grub >/dev/null 2>&1; then gen="update-grub"
        elif command -v grub2-mkconfig >/dev/null 2>&1; then gen="grub2-mkconfig"
        elif command -v grub-mkconfig >/dev/null 2>&1; then gen="grub-mkconfig"; fi
    fi

    # 1) Boot entries via grubby where it works. It edits BLS entries and legacy grub in place;
    #    grub2-mkconfig does not touch BLS entries on RHEL 9.3+ (GRUB_ENABLE_BLSCFG=true).
    if [ "$USE_GRUBBY" = 1 ]; then
        if [ -n "$values" ]; then
            for v in $values; do
                grubby --update-kernel=ALL --remove-args="nvme_core.io_timeout=${v}" 2>/dev/null
                grubby --update-kernel=ALL --remove-args="nvme.io_timeout=${v}" 2>/dev/null
            done
        fi
        grubby --update-kernel=ALL --args="${param}"
        echo "Updated all kernel boot entries with grubby."
    fi

    # 2) Persistent default configuration, so kernels installed later inherit the setting.
    if [ "$gen" = update-grub ] && [ -d /etc/default/grub.d ]; then
        # Ubuntu/Debian cloud images set GRUB_CMDLINE_LINUX_DEFAULT in a grub.d drop-in that
        # overrides /etc/default/grub, and with GRUB_FORCE_PARTUUID the booted initrdless entry
        # reads only _DEFAULT. A 99- drop-in is sourced last, so the booted entry gets it.
        local dropin=/etc/default/grub.d/99-nvme-io-timeout.cfg
        printf 'GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT %s"\n' "$param" > "$dropin"
        echo "Wrote ${dropin}"
    elif [ -f /etc/default/grub ]; then
        cp -a /etc/default/grub "/etc/default/grub.backup.${time_stamp}"
        backup_note="Original /etc/default/grub saved as /etc/default/grub.backup.${time_stamp}"
        if grep -qE '^GRUB_CMDLINE_LINUX=' /etc/default/grub; then
            grub_default_add_param GRUB_CMDLINE_LINUX "$param"
        else
            grub_default_add_param GRUB_CMDLINE_LINUX_DEFAULT "$param"
        fi
        echo "Updated /etc/default/grub. ${backup_note}"
    fi

    # 3) Regenerate grub.cfg where the bootloader reads it directly. Never eval a bare
    #    redirection: an empty command name would truncate grub.cfg.
    if [ "$USE_GRUBBY" = 0 ]; then
        local cfg=""
        if [ "$gen" = update-grub ]; then
            update-grub
        elif [ -n "$gen" ]; then
            for cfg in /boot/grub2/grub.cfg /boot/grub/grub.cfg /boot/efi/EFI/*/grub.cfg; do
                [ -f "$cfg" ] && grep -qE '^[[:space:]]*(menuentry|linux|linuxefi|blscfg)' "$cfg" && break
                cfg=""
            done
            if [ -z "$cfg" ]; then
                fixfail "Could not identify which grub.cfg this system boots from; /etc/default/grub was updated but grub.cfg was not regenerated."
                note "Run ${gen} -o <path-to-your-grub.cfg> manually."
                echo "***********************"; return
            fi
            cp -a "$cfg" "${cfg}.backup.${time_stamp}"
            echo "Original ${cfg} saved as ${cfg}.backup.${time_stamp}"
            "$gen" -o "$cfg"
        else
            fixfail "No grubby, update-grub, grub2-mkconfig or grub-mkconfig found; cannot regenerate the bootloader configuration."
            echo "***********************"; return
        fi
    fi

    # Re-verify from the same sources, requiring every entry this time as well
    timeout_coverage
    if [ "$TOTAL" -gt 0 ] && [ "$WITH" -eq "$TOTAL" ]; then
        ok "NVMe io_timeout=${NVME_MAX} is now set on all ${TOTAL} kernel boot entries. It takes effect on the next reboot."
        ISSUES=$((ISSUES-1))
    else
        fixfail "NVMe io_timeout is set on ${WITH} of ${TOTAL} boot entries after the change; could not confirm it everywhere."
    fi
    echo "***********************"
}

########################################################################

check_ena_driver () {
    local state version
    state=$(module_state ena)
    if [ "$state" = missing ]; then
        err "ENA driver is not available on your instance."
        note "Install the ENA driver before changing your instance type to Nitro. See:"
        note "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/enhanced-networking-ena.html"
        return
    fi
    version=$(modinfo -F version ena 2>/dev/null | head -1)
    if [ -n "$version" ]; then
        ok "ENA driver version ${version} is installed (${state})"
    else
        ok "ENA driver is installed (${state}, in-tree driver shipped with kernel ${KVER})"
    fi
}

########################################################################

check_fstab () {
    local time_stamp tmp_new tmp_dev dev resolved uuid changed=0 unresolved=0
    time_stamp=$(date +%F-%H:%M:%S)
    tmp_new=$(mktemp /tmp/fstab.new.XXXXXX) || return
    tmp_dev=$(mktemp /tmp/fstab.dev.XXXXXX) || { rm -f "$tmp_new"; return; }
    trap 'rm -f "$tmp_new" "$tmp_dev"' RETURN

    # First field of every non-comment line that is a /dev/sd* or /dev/xvd* name
    awk '$0 !~ /^[[:space:]]*#/ && $1 ~ /^\/dev\/(sd|xvd)[a-z]+[0-9]*$/ {print $1}' /etc/fstab | sort -u > "$tmp_dev"

    if [ ! -s "$tmp_dev" ]; then
        ok "fstab does not mount anything by /dev/sd* or /dev/xvd* device name"
        return
    fi

    cp /etc/fstab "$tmp_new"
    while read -r dev; do
        # follow udev symlinks (/dev/sdf points to xvdf, or to nvme1n1 on Nitro) to the real device
        resolved=$(readlink -f "$dev" 2>/dev/null)
        uuid=""
        if [ -b "$resolved" ]; then
            uuid=$(blkid -s UUID -o value "$resolved" 2>/dev/null)
            [ -z "$uuid" ] && uuid=$(lsblk -no UUID "$resolved" 2>/dev/null | head -1)
        fi
        if [ -n "$uuid" ]; then
            # Replace field 1 exactly (so /dev/xvdf never rewrites a /dev/xvdf1 line)
            awk -v d="$dev" -v u="UUID=${uuid}" '$0 !~ /^[[:space:]]*#/ && $1 == d {sub(/^[[:space:]]*[^[:space:]]+/, u)} {print}' "$tmp_new" > "${tmp_new}.1" && mv "${tmp_new}.1" "$tmp_new"
            changed=$((changed+1))
            echo "  ${dev} -> UUID=${uuid}  (${resolved})"
        else
            unresolved=$((unresolved+1))
            echo "  ${dev}: no filesystem UUID found (device absent or has no filesystem); left unchanged"
        fi
    done < "$tmp_dev"

    err "fstab mounts by device name. Device names change on Nitro (/dev/nvme*), so mount by UUID instead."
    if [ "$changed" -eq 0 ]; then
        note "None of the entries could be converted automatically; edit /etc/fstab by hand."
        return
    fi
    echo -e "\nProposed /etc/fstab:\n"; cat "$tmp_new"
    if confirm "Replace the ${changed} device-name entries in /etc/fstab with their UUIDs?"; then
        cp -a /etc/fstab "/etc/fstab.backup.${time_stamp}"
        cp "$tmp_new" /etc/fstab
        echo -e "\nWritten. Original fstab saved as /etc/fstab.backup.${time_stamp}"
        [ "$unresolved" -eq 0 ] && ISSUES=$((ISSUES-1))
    fi
}

########################################################################
# Main

if [ "$(id -u)" -ne 0 ]; then
    echo -e "------------------------------------------------"
    echo -e "\nThis script must be run as root" >&2
    echo -e "\n------------------------------------------------"
    exit 1
fi

echo -e "------------------------------------------------"
echo -e "Kernel: ${KVER}   Mode: ${MODE}"

check_nvme_driver
check_nvme_timeout
check_ena_driver
check_fstab

echo -e "\n------------------------------------------------"
if [ "$ISSUES" -gt 0 ]; then
    echo "${ISSUES} item(s) need attention before changing to a Nitro instance type."
    exit 2
fi
echo "All checks passed."
exit 0
