#!/bin/sh
# Temporary live trial only. No boot or root-partition changes.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
BASE=/var/local/calendar-appliance-trial
STATE=/tmp/calendar-appliance-trial-4

stop_app() {
    service=$1
    name=$service
    [ "$service" = webreaderd ] && name=webreader
    /usr/bin/lipc-set-prop com.lab126.pmond stop "$name"
    # Avoid the suspected old killall match of its calling init shell script.
    # Signal only PIDs whose executable is the actual application binary.
    for app_pid in $(pidof "$name"); do
        if [ "$(readlink /proc/$app_pid/exe)" = "/usr/bin/$name" ]; then
            kill -TERM "$app_pid"
            sleep 1
            if [ "$(readlink /proc/$app_pid/exe)" = "/usr/bin/$name" ]; then
                kill -KILL "$app_pid"
            fi
        fi
    done
}

restore() {
    mkdir "$STATE/restoring" 2>/dev/null || return 0
    echo RESTORE_BEGIN
    touch "$BASE/data/DISABLED"
    sleep 12
    for target in sys proc dev; do
        if [ -f "$STATE/bound-$target" ]; then
            umount "$BASE/$target" || echo "UNMOUNT_FAILED $target"
        fi
    done
    for service in webreaderd browserd framework; do
        if [ -f "$STATE/stopped-$service" ]; then
            /etc/init.d/"$service" start
        fi
    done
    if [ -f "$STATE/overlay-running" ]; then
        /etc/init.d/calendar-display start
    fi
    touch "$STATE/restored"
    echo RESTORE_COMPLETE
}

case "$1" in
    rollback)
        trap '' HUP
        sleep 600
        restore
        ;;
    restore-now)
        trap '' HUP
        restore
        ;;
    start)
        set -e
        test -d "$BASE"
        test ! -e "$BASE/data/DISABLED"
        test ! -e /mnt/us/DONT_START_FRAMEWORK
        mkdir "$STATE"
        /bin/sh /mnt/us/calendar-display/service.sh status | grep -q 'running pid=' && touch "$STATE/overlay-running"
        # Arm a detached recovery process before stopping any services.
        /bin/sh "$BASE/trial.sh" rollback > "$STATE/rollback.log" 2>&1 < /dev/null &
        echo $! > "$STATE/rollback.pid"
        sleep 1
        kill -0 "$(cat "$STATE/rollback.pid")"
        /etc/init.d/calendar-display stop
        cp "$BASE/update-test.png" "$BASE/data/current.png"
        for target in dev proc sys; do
            mount --bind /"$target" "$BASE/$target"
            touch "$STATE/bound-$target"
        done
        chroot "$BASE" /usr/sbin/eips -f -g /data/current.png
        echo ISOLATED_RENDER_OK
        for service in framework browserd webreaderd; do
            touch "$STATE/stopped-$service"
            if [ "$service" = framework ]; then
                /etc/init.d/framework stop
            else
                stop_app "$service"
            fi
        done
        test ! -d "$STATE/restoring"
        /bin/sh "$BASE/power-state.sh" > "$STATE/power-state.log" 2>&1 < /dev/null &
        echo $! > "$STATE/power-state.pid"
        chroot "$BASE" /bin/sh /sbin/display-supervisor > "$STATE/supervisor.log" 2>&1 < /dev/null &
        echo $! > "$STATE/supervisor.pid"
        sleep 2
        kill -0 "$(cat "$STATE/supervisor.pid")"
        echo APPLIANCE_TRIAL_RUNNING
        ;;
    *) exit 2 ;;
esac
