#!/bin/sh
# Application supervisor inside the staged userspace, not a replacement PID 1.
PATH=/bin:/usr/sbin
export PATH
trap 'exit 0' TERM INT
trap '' HUP
last=''
last_refresh=''
while [ ! -e /data/DISABLED ]; do
    if [ -s /data/current.png ]; then
        current=$(md5sum /data/current.png)
        refresh=''
        [ ! -f /data/refresh ] || refresh=$(cat /data/refresh)
        if [ "$current" != "$last" ] || [ "$refresh" != "$last_refresh" ]; then
            if /usr/sbin/eips -f -g /data/current.png; then
                last=$current
                last_refresh=$refresh
                echo "RENDER_OK image=$current refresh=$refresh"
                power_state=${refresh#* Powerd state: }
                case "$power_state" in
                    Active) symbol=On ;;
                    'Screen Saver'|'Ready to suspend'|Suspended|Shutdown) symbol=zZ ;;
                    *) symbol='' ;;
                esac
                if [ -n "$symbol" ]; then
                    # K4 text cells are 12 by 20 pixels. Keep clear of the date range.
                    if /usr/sbin/eips 46 2 "$symbol"; then
                        echo "POWER_OVERLAY_OK state=$power_state symbol=$symbol"
                    else
                        echo "POWER_OVERLAY_FAILED state=$power_state symbol=$symbol"
                    fi
                fi
            else
                echo "RENDER_FAILED image=$current refresh=$refresh"
            fi
        fi
    fi
    sleep 5
done
echo SUPERVISOR_EXIT
