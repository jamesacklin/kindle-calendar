#!/bin/sh
# One-shot experiment invoked by the installed USBNetwork init hook.
BASE=/var/local/calendar-usb-boot-test-4
if [ -f "$BASE/ARM" ]; then
    mv "$BASE/ARM" "$BASE/CONSUMED" || exit 1
    # Internal worker waits for daemon readiness without blocking stock init.
    /bin/sh "$BASE/worker.sh" start > "$BASE/boot.log" 2>&1 < /dev/null &
fi
exit 0
