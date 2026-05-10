#!/bin/bash

echo
echo "Advanced Security & Configuration Check"
echo

echo "IPv6 Firewall rules (ip6tables):"
if command -v ip6tables >/dev/null 2>&1; then
    ip6tables -L -v | head -10
else
    echo "ip6tables not found"
fi
echo

echo "Persistent Firewall rules check:"
ls -l /etc/network/if-pre-up.d/iptables /etc/iptables.up.rules 2>/dev/null || echo "No standard persistent iptables rules found."
echo

echo "Filesystem mount options (/etc/fstab):"
grep -E "noatime|noexec|nosuid" /etc/fstab || echo "No secure mount options (noatime, noexec, nosuid) found in fstab."
echo

echo "Password encryption algorithms (/etc/shadow):"
if [ -r /etc/shadow ]; then
    grep -E '^\w+:\$1\$' /etc/shadow >/dev/null && echo "WARNING: MD5 hashes found!"
    grep -E '^\w+:\$6\$' /etc/shadow >/dev/null && echo "SHA-512 hashes are in use (Good)."
    grep -E '^\w+:[^\$:]' /etc/shadow >/dev/null && echo "WARNING: Possible DES hashes found!"
    echo "Shadow file check completed."
else
    echo "Cannot read /etc/shadow (run script with sudo if you want to check this)"
fi
echo

echo "Advanced SSH settings (/etc/ssh/sshd_config):"
if [ -f /etc/ssh/sshd_config ]; then
    grep -i "^AllowTcpForwarding" /etc/ssh/sshd_config || echo "AllowTcpForwarding not explicitly set."
    grep -i "^Port " /etc/ssh/sshd_config || echo "Default SSH Port might be in use."
else
    echo "sshd_config not found."
fi
echo

echo "done"