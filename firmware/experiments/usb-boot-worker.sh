#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
trap '' HUP
BASE=/var/local/calendar-usb-boot-test-2
USB=/mnt/us/usbnet/bin/usbnetwork
case "$1" in
    fallback)
        sleep 180
        if [ -f "$BASE/ACK" ]; then
            echo USB_BOOT_ACKNOWLEDGED
        else
            echo USB_BOOT_FALLBACK_TO_STORAGE
            if lsmod | grep -q g_ether; then
                /bin/sh "$USB" usbms
                echo "FALLBACK_EXIT=$?"
            else
                echo ALREADY_STORAGE
            fi
        fi
        ;;
    start)
        echo USB_BOOT_TEST_STARTED
        # Called synchronously at S82, before the user volume is exported.
        /bin/sh "$BASE/worker.sh" fallback > "$BASE/fallback.log" 2>&1 < /dev/null &
        echo $! > "$BASE/fallback.pid"
        sleep 1
        kill -0 "$(cat "$BASE/fallback.pid")" || exit 1
        if lsmod | grep -q g_ether; then
            echo USB_ALREADY_NETWORK
        else
            /bin/sh "$USB"
            result=$?
            echo "USB_START_EXIT=$result"
            [ "$result" -eq 0 ] || exit "$result"
        fi
        ifconfig usb0 || exit 1
        echo USB_BOOT_TEST_READY
        ;;
    *) exit 2 ;;
esac
