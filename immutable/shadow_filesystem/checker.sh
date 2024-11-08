#!/bin/bash

<<COMMENT
This file handles the periodic check functionality of the shadow filesystem module.
It is called every X minutes via some manner of persistence.
It compares the 
COMMENT

# Redirect all output to both terminal and log file
exec > >(tee -a checker.log) 2>&1

# Import variables
resultsPath="./variables.sh"
if [ -f $resultsPath ] ; then
    source $resultsPath
else
    echo "Variables file does not exist in current directory!"
    exit
fi

live_dir="/path/to/directory1/"
archive_dir=$hid_dir

# Iterate over all files in archive directory
find "$archive_dir" -type f | while read -r archive_file; do
    # Get the relative path of the file with respect to archive_dir
    relative_path="${archive_file#$archive_dir/}"
    live_file="$live_dir/$relative_path"

    # Check if the file exists in live directory
    if [ ! -e "$live_file" ]; then
        # File doesn't exist in live directory, copy from archive directory
        echo "Copying $archive_file to $live_file (file does not exist in live directory)"
        mkdir -p "$(dirname "$live_file")"  # Create the target directory if it doesn't exist
        cp "$archive_file" "$live_file"
    else
        # Check if the modification times are different
        mod_time1=$(stat -c %Y "$live_file")
        mod_time2=$(stat -c %Y "$archive_file")
        if [ "$mod_time1" -ne "$mod_time2" ]; then
            # Timestamps are different, copy from archive directory
            echo "Copying $archive_file to $live_file (modified time differs)"
            cp "$archive_file" "$live_file"
        fi
    fi
done