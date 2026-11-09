#!/bin/sh
# Prototype fallback: observe retained powerd state, no power settings changed.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
DATA=${DATA:-/var/local/calendar-appliance-trial/data}
trap 'exit 0' TERM INT
trap '' HUP
last=''
sequence=0
while [ ! -e "$DATA/DISABLED" ]; do
    status=$(lipc-get-prop com.lab126.powerd status 2>/dev/null)
    state=$(echo "$status" | sed -n '1p')
    case "$state" in
        'Powerd state: '*)
            if [ "$state" != "$last" ]; then
                echo "POWER_STATE $state"
                sequence=$((sequence + 1))
                echo "state-$sequence $state" > "$DATA/refresh.new"
                mv "$DATA/refresh.new" "$DATA/refresh"
                last=$state
            fi
            ;;
    esac
    sleep 2
done
echo POWER_BRIDGE_EXIT
