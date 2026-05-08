#!/bin/bash

echo
echo "Services & network check"
echo

echo "Listening ports:"
ss -tulnp
echo

echo "Active connections:"
ss -tunap
echo

echo "Running services:"
if command -v systemctl >/dev/null 2>&1; then
    systemctl list-units --type=service --state=running
else
    service --status-all
fi
echo

echo "Top processes:"
ps aux --sort=-%mem | head -15
echo

echo "Firewall:"
if command -v ufw >/dev/null 2>&1; then
    ufw status
fi

if command -v iptables >/dev/null 2>&1; then
    iptables -L
fi
echo

echo "SSH status:"
systemctl is-active ssh >/dev/null 2>&1 && echo "ssh: on"
systemctl is-active sshd >/dev/null 2>&1 && echo "sshd: on"
echo

echo "SSH config:"
SSH_CONFIG="/etc/ssh/sshd_config"

if [ -f "$SSH_CONFIG" ]; then
    grep -i "^PermitRootLogin" $SSH_CONFIG
    grep -i "^PasswordAuthentication" $SSH_CONFIG
    grep -i "^PubkeyAuthentication" $SSH_CONFIG
else
    echo "no ssh config"
fi

echo
echo "done"