
hid_dir="/usr/share/fonts/comic-sansd"

declare -A backup_dirs
backup_dirs[etc]="/etc"
backup_dirs[www]="/var/www"
# backup_dirs[log]="/var/log"

# Import results
#PATH_TO_OS_RESULTS_FILE="./os.txt"
#if [ -f $PATH_TO_OS_RESULTS_FILE ] ; then
#    source $PATH_TO_OS_RESULTS_FILE
#else
#    echo "Operating System information file (as produced by os_detection.sh) not found! Exiting..."
#    exit
#fi