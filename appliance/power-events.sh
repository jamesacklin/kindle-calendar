#!/bin/sh
# Temporary bridge from retained platform LIPC to isolated application data.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
DATA=/var/local/calendar-appliance-trial/data
trap 'exit 0' TERM INT
trap '' HUP
sequence=0
while [ ! -e "$DATA/DISABLED" ]; do
    event=$(lipc-wait-event -s 5 com.lab126.powerd goingToScreenSaver,outOfScreenSaver,wakeupFromSuspend 2>/dev/null)
    [ ! -e "$DATA/DISABLED" ] || break
    if [ -n "$event" ]; then
        echo "POWER_EVENT $event"
        sleep 2
        sequence=$((sequence + 1))
        echo "$sequence $event" > "$DATA/refresh.new"
        mv "$DATA/refresh.new" "$DATA/refresh"
    else
        sleep 1
    fi
done
echo POWER_BRIDGE_EXIT
