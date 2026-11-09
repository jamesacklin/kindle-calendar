#!/bin/sh
BASE=/var/local/calendar-appliance
if [ -f "$BASE/ENABLED" ]; then
    /bin/sh "$BASE/manage.sh" boot > /tmp/calendar-appliance-boot.log 2>&1 < /dev/null &
fi
exit 0
