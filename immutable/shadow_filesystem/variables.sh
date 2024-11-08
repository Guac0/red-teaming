#!/bin/bash

hid_dir="/usr/share/fonts/comic-sansd/"

declare -A backup_dirs
# backup_dirs[etc]="/etc/"
backup_dirs[www]="/var/www/"
# backup_dirs[log]="/var/log/"

# Import variables
resultsPath="./variables.sh"
if [ -f $resultsPath ] ; then
    source $resultsPath
else
    echo "Variables file does not exist in current directory!"
    exit
fi