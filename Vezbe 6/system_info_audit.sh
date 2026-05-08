#!/bin/bash

echo
 echo "System information check"
 echo

 echo "Hostname:"
 hostname
 echo

 echo "OS version:"
 cat /etc/os-release 2>/dev/null
 echo

 echo "Kernel version:"
 uname -a
 echo

 echo "System uptime:"
 uptime
 echo

 echo "Current users logged in:"
 who
 echo

 echo "Timezone:"
 timedatectl 2>/dev/null | grep "Time zone"
 echo

 echo "NTP status:"
 timedatectl status 2>/dev/null | grep "NTP"
 echo

 echo "Disk usage:"
 df -h
 echo

 echo "Mounted filesystems:"
 mount | head -20
 echo

 echo "Installed packages count:"
 if command -v dpkg >/dev/null 2>&1; then
     dpkg -l | wc -l
 elif command -v rpm >/dev/null 2>&1; then
     rpm -qa | wc -l
 else
     echo "package manager not found"
 fi
 echo

 echo "Cron jobs:"
 ls -l /etc/cron* 2>/dev/null
 echo

 echo "done"