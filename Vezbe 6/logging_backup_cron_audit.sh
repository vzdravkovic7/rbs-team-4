#!/bin/bash

echo
echo "Logging, Backup & Scheduled Tasks check"
echo

echo "Logging service (rsyslog) status:"
ps -edf | grep syslog | grep -v grep
echo

echo "Remote logging configuration in rsyslog:"
if [ -f /etc/rsyslog.conf ]; then
    grep -E "^[^#].*@.*|^[^#].*imudp|^[^#].*imtcp" /etc/rsyslog.conf || echo "No active remote logging found."
else
    echo "/etc/rsyslog.conf not found."
fi
echo

echo "Backup directories permissions:"
ls -ld /backup /var/backups 2>/dev/null
echo

echo "World-readable files in /backup:"
find /backup -type f -perm -0004 2>/dev/null | head -10
echo

echo "User crontabs (/var/spool/cron/crontabs):"
ls -l /var/spool/cron/crontabs 2>/dev/null
echo

echo "World-writable scripts in cron directories:"
find /etc/cron* -type f -perm -0002 2>/dev/null
echo

echo "done"