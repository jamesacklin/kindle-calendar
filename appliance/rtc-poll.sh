#!/bin/sh
# Kindle 4 calendar polling with a hardware wake alarm on battery.
PATH=/usr/bin:/bin
export PATH
BASE=/var/local/calendar-appliance
STATE=/tmp/calendar-appliance
RTC=/sys/devices/platform/mxc_rtc.0/wakeup_enable
CLOCK=/sys/class/rtc/rtc0/since_epoch
url=${1:-}
interval=${2:-900}
limit=${3:-0}
case "$url" in http://*|https://*) ;; *) exit 2 ;; esac
case "$interval:$limit" in *[!0-9:]*|*:*:*) exit 2 ;; esac
[ "$interval" -ge 60 ] && [ "$limit" -ge 0 ] || exit 2

stamp() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*"; }
charging() { lipc-get-prop com.lab126.powerd isCharging 2>/dev/null; }
ready() {
    [ -f "$STATE/READY" ] && [ ! -d "$STATE/restoring" ] &&
        { [ "$limit" -gt 0 ] || [ -f "$BASE/RTC_POLL" ]; }
}
battery_safe() {
    [ "$(charging)" = 0 ] || return 1
    level=$(lipc-get-prop com.lab126.powerd battLevel 2>/dev/null)
    case "$level" in ''|*[!0-9]*) return 1 ;; esac
    [ "$level" -ge 20 ]
}

original_saver=
owned_alarm=
clear_alarm() {
    if [ -n "$owned_alarm" ] && [ "$(cat "$RTC" 2>/dev/null)" = "$owned_alarm" ]; then
        printf '0\n' > "$RTC"
    fi
    owned_alarm=
}
restore_saver() {
    if [ -n "$original_saver" ]; then
        lipc-set-prop -i com.lab126.powerd preventScreenSaver "$original_saver" || return 1
        original_saver=
    fi
}
cleanup() {
    clear_alarm
    restore_saver
}
trap cleanup EXIT
trap 'exit 0' TERM INT
trap '' HUP

poll() {
    if [ -n "$original_saver" ]; then
        lipc-set-prop -i com.lab126.wifid enable 1 >/dev/null 2>&1 || :
    fi
    for attempt in 1 2 3; do
        ready || return 1
        if /bin/sh "$BASE/poll-image.sh" once "$url"; then
            stamp "POLL_OK attempt=$attempt"
            return 0
        fi
        stamp "POLL_RETRY attempt=$attempt"
        [ "$attempt" -eq 3 ] || sleep 5
    done
    stamp POLL_FAILED
    return 1
}

suspend_for() {
    delay=$1
    current_alarm=$(cat "$RTC") || return 1
    if [ "$current_alarm" != 0 ]; then
        stamp "RTC_BUSY value=$current_alarm"
        return 1
    fi
    sync
    ready && battery_safe || return 0
    printf '%s\n' "$delay" > "$RTC" || return 1
    owned_alarm=$delay
    [ "$(cat "$RTC")" = "$delay" ] || return 1
    stamp "RTC_SUSPEND seconds=$delay"
    echo mem > /sys/power/state || return 1
    after=$(cat "$CLOCK") || return 1
    clear_alarm
    stamp "RTC_RESUME elapsed=$((after - now))"
    if [ "$after" -lt "$next_poll" ] && battery_safe; then
        early_wakes=$((early_wakes + 1))
        [ "$early_wakes" -lt 5 ] || return 1
        sleep 2
    fi
}

now=$(cat "$CLOCK") || exit 1
next_poll=$((now + interval))
test_deadline=$((now + 180))
cycles=0
failures=0
early_wakes=0
stamp "RTC_POLLER_READY interval=$interval limit=$limit"

while ready; do
    now=$(cat "$CLOCK") || break
    if battery_safe; then
        if [ -z "$original_saver" ]; then
            saved=$(lipc-get-prop com.lab126.powerd preventScreenSaver 2>/dev/null)
            case "$saved" in 0|1) original_saver=$saved ;; *) break ;; esac
            lipc-set-prop -i com.lab126.powerd preventScreenSaver 1 || break
            settle_until=$((now + 60))
            early_wakes=0
            stamp BATTERY_SETTLING
            if [ "$limit" -gt 0 ]; then
                next_poll=$((settle_until + interval))
            fi
        fi
        if [ "$now" -lt "$settle_until" ]; then
            sleep 5
            continue
        fi
        if [ "$now" -lt "$next_poll" ]; then
            suspend_for "$((next_poll - now))" || break
            continue
        fi
    else
        if [ "$limit" -gt 0 ]; then
            [ -z "$original_saver" ] && [ "$now" -lt "$test_deadline" ] || exit 1
            sleep 5
            continue
        fi
        restore_saver || break
        if [ "$now" -lt "$next_poll" ]; then
            sleep 5
            continue
        fi
    fi

    early_wakes=0
    next_poll=$((now + interval))
    poll || failures=$((failures + 1))
    # Let the display supervisor pick up an updated PNG before suspending.
    sleep 10
    if [ "$limit" -gt 0 ]; then
        cycles=$((cycles + 1))
        if [ "$cycles" -ge "$limit" ]; then
            stamp "RTC_TEST_DONE cycles=$cycles failures=$failures"
            [ "$failures" -eq 0 ]
            exit $?
        fi
    fi
done

[ "$limit" -eq 0 ] || exit 1
cleanup
trap - EXIT
[ -f "$STATE/READY" ] && [ ! -d "$STATE/restoring" ] || exit 0
stamp RTC_FALLBACK_TO_REGULAR_POLLING
exec /bin/sh "$BASE/poll-image.sh" loop "$url" "$interval"
