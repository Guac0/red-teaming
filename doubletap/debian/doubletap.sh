fuse_date="2025-03-21"  # In format YYYY-MM-DD
fuse_time="16:00:00"    # In format HH:MM:SS, using 24h time
fuse_armed="false"      # DO NOT SET THIS TO TRUE UNLESS YOU WANT TO EXPLODE
debug="false"           # 

#########################
###### TIME CHECK #######
#########################
today=$(date +"%Y-%m-%d")
current_hour=$(date +"%H")

if [ "$debug" = "true" ]; then
    echo "---------------------------------------------"
    echo "  Timebomb - $today $current_hour"
fi

# Check if the date is March 21st, 2025, and the time is after 3 PM
if [ "$today" = "$fuse_date" ]; then
    if [ "$fuse_time" -ge $current_hour ]; then
        if [ "$debug" = "true" ]; then
            echo "+++++++++++++++++++++++++++++++++++"
            echo "  DETONATION CRITERIA MET"
            echo "Found date $today and expected $fuse_date"
            echo "Found hour $current_hour and expected $fuse_hour"
            if [ "$fuse_armed" = "true" ]; then 
                echo "  PROCEEDING WITH FULL KABOOM"
            else
                echo "  ... where's the kaboom? FUSE NOT ARMED"
            fi
        fi

        if [ "$fuse_armed" = "true" ]; then
            # Kaboom

            # Delete persistance/kill this task
            # doesn't matter if blue team finds this because they can just delete this file
            # todo: unless this file is stabvested. stabvest should contain an auto-off after the fuse time
        fi
    else 
        if [ "$debug" = "true" ]; then
            echo "Wrong hour - found $today but expected $current_hour"
        fi
    fi
else
    if [ "$debug" = "true" ]; then
        echo "Wrong date - found $today but expected $fuse_date"
    fi
fi
