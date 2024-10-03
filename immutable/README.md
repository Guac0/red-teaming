# Immutable
Working title.

A tool suite that attempts to prevent changes to the local file system. Designed to be primarily a Red Team tool but also works as a Blue Team suite.

Intended to be dropped on a system after you finish your own work on it (Blue team - drop after finish hardening, Red team - drop after finish compromising and adding persistence).

Features
* Watches important directories (/etc, /var/html) for changes and reverts them (including reverting services to prior config states) 
* Monitors user commands and deploys countermeasures as necessary
    * Common file edit commands result in the original file being backed up and restored after editor exit
    * Service status change commands are automatically reverted
    * CURL and GIT CLONE result in downloaded data being stashed for analysis (optionally also deleted)
    * Logging all actions and optionally sending them to a log server for analysis
    * Multifaceted persistence