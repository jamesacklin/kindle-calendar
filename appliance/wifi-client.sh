#!/bin/sh
# Opt-in boot handoff: prove the image endpoint before confirming this boot.
PATH=/usr/bin:/bin
export PATH
BASE=/var/local/calendar-appliance
STATE=/tmp/calendar-appliance
URL=$(sed -n '1p' "$BASE/IMAGE_URL") || exit 1
case "$URL" in
    http://*|https://*) ;;
    *) echo INVALID_IMAGE_URL; exit 1 ;;
esac

attempt=0
while [ "$attempt" -lt 24 ]; do
    [ ! -d "$STATE/restoring" ] || exit 1
    if ! ifconfig wlan0 | grep -q 'inet addr:'; then
        lipc-set-prop -i com.lab126.powerd wakeUp 1 >/dev/null 2>&1
        sleep 5
    fi
    if /bin/sh "$BASE/poll-image.sh" once "$URL"; then
        /bin/sh "$BASE/manage.sh" confirm || exit 1
        echo WIFI_CLIENT_READY
        exec /bin/sh "$BASE/poll-image.sh" loop "$URL" 900
    fi
    attempt=$((attempt + 1))
    sleep 10
done
echo WIFI_CLIENT_TIMED_OUT
exit 1
