#!/bin/bash

echo
 echo "Web & database configuration check"
 echo

 echo "Apache/Nginx processes:"
 ps aux | egrep 'apache2|nginx' | grep -v grep
 echo

 echo "MySQL/MariaDB processes:"
 ps aux | egrep 'mysql|mariadb' | grep -v grep
 echo

 echo "Web server ports:"
 ss -tulnp | egrep ':80|:443|:3306'
 echo

 echo "Apache security config:"
 if [ -f /etc/apache2/conf-enabled/security.conf ]; then
     grep -i "ServerTokens\|ServerSignature" /etc/apache2/conf-enabled/security.conf
 elif [ -f /etc/apache2/conf.d/security ]; then
     grep -i "ServerTokens\|ServerSignature" /etc/apache2/conf.d/security
 else
     echo "apache security config not found"
 fi
 echo

 echo "PHP settings:"
 PHPINI="/etc/php/php.ini"

 if [ -f "$PHPINI" ]; then
     grep -E "display_errors|log_errors|expose_php|allow_url_include" "$PHPINI"
 else
     find /etc/php* -name php.ini 2>/dev/null | head -1 | while read file; do
         echo "using: $file"
         grep -E "display_errors|log_errors|expose_php|allow_url_include" "$file"
     done
 fi
 echo

 echo "Web root permissions:"
 ls -ld /var/www 2>/dev/null
 find /var/www -type f -perm -0002 2>/dev/null | head -20
 echo

 echo "MySQL config:"
 if [ -f /etc/mysql/my.cnf ]; then
     grep -i "bind-address" /etc/mysql/my.cnf
 else
     echo "mysql config not found"
 fi
 echo

 echo "done"