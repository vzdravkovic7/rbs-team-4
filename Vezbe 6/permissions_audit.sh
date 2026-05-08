#!/bin/bash

echo
echo "Users & permissions check"
echo

echo "UID 0 users:"
awk -F: '($3 == 0) {print "- " $1}' /etc/passwd
echo

echo "sudo group:"
getent group sudo 2>/dev/null | cut -d: -f4
echo

echo "wheel group:"
getent group wheel 2>/dev/null | cut -d: -f4
echo

echo "SUID files (top 20):"
find / -perm -4000 -type f 2>/dev/null | head -20
echo

echo "SGID files (top 20):"
find / -perm -2000 -type f 2>/dev/null | head -20
echo

echo "World writable files (top 20):"
find / -type f -perm -0002 2>/dev/null | head -20
echo

echo "World writable dirs (top 20):"
find / -type d -perm -0002 2>/dev/null | head -20
echo

echo "authorized_keys:"
find /home -name authorized_keys 2>/dev/null
echo

echo "important file perms:"
ls -l /etc/passwd /etc/shadow /etc/sudoers 2>/dev/null
echo

echo "done"