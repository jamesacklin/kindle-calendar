#!/bin/sh
# Runtime-only Kindle 4 test: bounded image checks, five minutes apart.
PATH=/usr/bin:/bin
export PATH
RTC=/sys/devices/platform/mxc_rtc.0/wakeup_enable
CLOCK=/sys/class/rtc/rtc0/since_epoch
LOG=/tmp/calendar-appliance/rtc-five-minute.log
POLL=/var/local/calendar-appliance/poll-image.sh
URL=${2:-}
if [ -z "$URL" ]; then
    URL=$(sed -n '1p' /var/local/calendar-appliance/IMAGE_URL) || exit 1
fi
case "$URL" in http://*|https://*) ;; *) echo INVALID_IMAGE_URL >&2; exit 2 ;; esac
INTERVAL=300
MAX_CYCLES=${1:-4}
case "$MAX_CYCLES" in *[!0-9]*|'') echo INVALID_CYCLE_COUNT >&2; exit 2 ;; esac
if [ "$MAX_CYCLES" -lt 1 ] || [ "$MAX_CYCLES" -gt 12 ]; then
    echo INVALID_CYCLE_COUNT >&2
    exit 2
fi
trap '' HUP

stamp() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }
charging() { lipc-get-prop com.lab126.powerd isCharging 2>/dev/null; }
restore_powerd() {
    lipc-set-prop -i com.lab126.powerd preventScreenSaver "$original_saver" >/dev/null 2>&1
    stamp "EXIT restored_preventScreenSaver=$original_saver"
}

original_saver=$(lipc-get-prop com.lab126.powerd preventScreenSaver) || exit 1
case "$original_saver" in 0|1) ;; *) exit 1 ;; esac
trap restore_powerd EXIT
stamp "START original_preventScreenSaver=$original_saver rtc=$(cat "$RTC")"
lipc-set-prop -i com.lab126.powerd preventScreenSaver 1 >/dev/null 2>&1 || exit 1

# USB data is only used to launch us. Allow up to three minutes to unplug,
# then wait another minute for the charger interrupt to settle.
attempt=0
while [ "$(charging)" != 0 ] && [ "$attempt" -lt 36 ]; do
    sleep 5
    attempt=$((attempt + 1))
done
if [ "$(charging)" != 0 ]; then stamp ABORT_STILL_CHARGING; exit 1; fi
stamp USB_REMOVED
sleep 60
if [ "$(charging)" != 0 ]; then
    stamp ABORT_CHARGER_RETURNED
    exit 1
fi
stamp "USB_SETTLED battery=$(lipc-get-prop com.lab126.powerd battLevel)"

cycle=1
failures=0
while [ "$cycle" -le "$MAX_CYCLES" ]; do
    battery=$(lipc-get-prop com.lab126.powerd battLevel 2>/dev/null)
    case "$battery" in *[!0-9]*|'') stamp ABORT_BATTERY_UNKNOWN; exit 1 ;; esac
    if [ "$battery" -lt 20 ]; then stamp ABORT_LOW_BATTERY; exit 1; fi
    target=$(( $(cat "$CLOCK") + INTERVAL ))

    # A short spurious wake is not a completed five-minute cycle.
    while :; do
        if [ "$(charging)" != 0 ]; then stamp STOP_USB_RECONNECTED; exit 0; fi
        now=$(cat "$CLOCK") || exit 1
        remaining=$((target - now))
        [ "$remaining" -gt 0 ] || break
        value=$(cat "$RTC") || exit 1
        if [ "$value" != 0 ]; then
            stamp "ABORT_RTC_BUSY value=$value"
            exit 1
        fi
        printf '%s' "$remaining" > "$RTC" || exit 1
        value=$(cat "$RTC") || exit 1
        if [ "$value" != "$remaining" ]; then
            stamp "ABORT_RTC_READBACK expected=$remaining actual=$value"
            exit 1
        fi
        stamp "SUSPEND cycle=$cycle interval=$remaining now=$now target=$target"
        sync
        echo mem > /sys/power/state
        result=$?
        after=$(cat "$CLOCK") || exit 1
        stamp "RESUME cycle=$cycle result=$result after=$after elapsed=$((after - now)) rtc=$(cat "$RTC")"
        [ "$result" -eq 0 ] || exit 1
        if [ $((target - after)) -gt 0 ]; then
            stamp "EARLY_WAKE cycle=$cycle remaining=$((target - after))"
        fi
    done

    if [ "$(charging)" != 0 ]; then stamp STOP_USB_RECONNECTED; exit 0; fi
    lipc-set-prop -i com.lab126.wifid enable 1 >/dev/null 2>&1
    attempt=0
    while [ "$attempt" -lt 12 ]; do
        [ "$(lipc-get-prop com.lab126.wifid cmState 2>/dev/null)" = CONNECTED ] && break
        sleep 5
        attempt=$((attempt + 1))
    done
    if [ "$(lipc-get-prop com.lab126.wifid cmState 2>/dev/null)" = CONNECTED ] &&
       /bin/sh "$POLL" once "$URL" >> "$LOG" 2>&1; then
        stamp "POLL_OK cycle=$cycle"
        failures=0
    else
        stamp "POLL_FAILED cycle=$cycle"
        failures=$((failures + 1))
        if [ "$failures" -ge 3 ]; then stamp ABORT_THREE_FAILURES; exit 1; fi
    fi
    sleep 10
    cycle=$((cycle + 1))
done
stamp "DONE_CYCLES count=$MAX_CYCLES"
