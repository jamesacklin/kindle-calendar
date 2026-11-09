#!/bin/sh
# Kindle 4 display service. All working state stays in RAM or user storage.
BASE=/mnt/us/calendar-display
PIDFILE=/var/run/calendar-display.pid
LOG=/tmp/calendar-display.log
EVENTS=goingToScreenSaver,outOfScreenSaver,wakeupFromSuspend,readyToSuspend

enabled() {
    [ -f "$BASE/current.png" ] && [ ! -e "$BASE/DISABLED" ]
}

running() {
    [ -r "$PIDFILE" ] || return 1
    pid=$(cat "$PIDFILE")
    case "$pid" in ''|*[!0-9]*) return 1 ;; esac
    [ -r "/proc/$pid/cmdline" ] || return 1
    tr '\000' ' ' < "/proc/$pid/cmdline" | grep -q '/mnt/us/calendar-display/service.sh daemon'
}

draw() {
    enabled || return 0
    # Do not touch the user volume while it is exported to a USB host.
    status=$(lipc-get-prop com.lab126.powerd status 2>/dev/null)
    case "$status" in *drive_mode:on*) return 0 ;; esac
    /usr/sbin/eips -f -g "$BASE/current.png"
    result=$?
    echo "$(date): redraw exit=$result"
    return "$result"
}

case "$1" in
    start|boot)
        enabled || exit 0
        running && exit 0
        delay=0
        [ "$1" = boot ] && delay=35
        /bin/sh "$BASE/service.sh" daemon "$delay" > "$LOG" 2>&1 < /dev/null &
        echo $! > "$PIDFILE"
        ;;
    daemon)
        # Background only: never block init or change power/framework policy.
        trap 'exit 0' TERM INT
        sleep "${2:-0}"
        enabled || exit 0
        draw
        while enabled; do
            event=$(lipc-wait-event -s 60 com.lab126.powerd "$EVENTS" 2>/dev/null)
            if [ -n "$event" ]; then
                echo "$(date): $event"
                case "$event" in
                    *readyToSuspend*) draw ;;
                    *) sleep 2; draw ;;
                esac
            else
                # Prevent spinning if the event provider becomes unavailable.
                sleep 2
            fi
        done
        ;;
    stop)
        if running; then
            kill "$pid"
        fi
        ;;
    redraw)
        draw
        ;;
    status)
        if running; then echo "running pid=$pid"; else echo stopped; fi
        if enabled; then echo enabled; else echo disabled; fi
        ;;
    *)
        echo 'Usage: service.sh {start|boot|stop|redraw|status}' >&2
        exit 2
        ;;
esac
