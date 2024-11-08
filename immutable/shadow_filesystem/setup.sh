#!/bin/bash

<<COMMENT
This file handles the shadow filesystem functionally of the immutable suite.
Backs up the specified directories to our shadow filesystem location.
Adds the cron job to execute the status checker.
COMMENT

# Redirect all output to both terminal and log file
exec > >(tee -a setup.log) 2>&1

# check for root and exit if not found
if  [ "$EUID" -ne 0 ];
then
    echo "User is not root. Skill issue."
    exit
fi

# Import variables
resultsPath="./variables.sh"
if [ -f $resultsPath ] ; then
    source $resultsPath
else
    echo "Variables file does not exist in current directory!"
    exit
fi

# Make the backup directory
mkdir -p "$hid_dir"

# Backup the given directories
for key in "${!dirs[@]}"; do
    dir="${dirs[$key]}"
    if [ -d "$dir" ]; then
        echo "Backing up $key..."
        # rsync performs efficient copying by checking differences between files, only transferring new or changed data. It’s usually fast for most local copy tasks.
        # -a: Archive mode. This preserves symbolic links, permissions, timestamps, and recursively copies all files and directories.
        # --info=progress2: Displays progress information during the transfer.
        rsync -a --info=progress2 $dir $hid_dir/$dir
    fi
done

# Add the cronjob to root. every 5 min.
echo "*/5 * * * * $(pwd)/checker.sh" | sudo crontab -