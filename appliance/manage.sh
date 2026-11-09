#!/bin/sh
# Provisional appliance: retain stock boot/platform, replace running reader apps.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
trap '' HUP
BASE=/var/local/calendar-appliance
ROOT=$BASE/rootfs
STATE=/tmp/calendar-appliance

network_ready() {
    mode=$(lipc-get-prop com.lab126.volumd useUsbForNetwork 2>/dev/null) || return 1
    case "$mode" in 0|1) return 0 ;; *) return 1 ;; esac
}

network_start() {
    count=0
    until network_ready; do
        count=$((count + 1))
        [ "$count" -lt 90 ] || return 1
        sleep 1
    done
    echo "VOLUMD_READY seconds=$count"
    lipc-set-prop -i -- com.lab126.volumd useUsbForNetwork 1 || return 1
    count=0
    until [ -d /sys/class/net/usb0 ] && [ -x /usr/bin/dropbear ] && [ -r /mnt/us/usbnet/etc/authorized_keys ]; do
        count=$((count + 1))
        [ "$count" -lt 45 ] || return 1
        sleep 1
    done
    ifconfig usb0 192.168.15.244 netmask 255.255.255.0 up || return 1
    /usr/bin/dropbear -s -p 192.168.15.244:22 -P "$STATE/sshd.pid" -K 15 || return 1
    sleep 1
    kill -0 "$(cat "$STATE/sshd.pid")" || return 1
    echo NETWORK_READY
}

stop_app() {
    service=$1
    name=$service
    [ "$service" = webreaderd ] && name=webreader
    lipc-set-prop com.lab126.pmond stop "$name" || return 1
    for app_pid in $(pidof "$name"); do
        if [ "$(readlink /proc/$app_pid/exe)" = "/usr/bin/$name" ]; then
            kill -TERM "$app_pid"
            sleep 1
            if [ "$(readlink /proc/$app_pid/exe)" = "/usr/bin/$name" ]; then
                kill -KILL "$app_pid"
            fi
        fi
    done
    return 0
}

application_start() {
    # Wait for stock reader startup before taking over; avoid racing its boot draw.
    count=0
    until lipc-get-prop com.lab126.framework isRegistered > /dev/null 2>&1; do
        count=$((count + 1))
        [ "$count" -lt 90 ] || return 1
        sleep 1
    done
    sleep 40
    [ ! -d "$STATE/restoring" ] || return 1
    test -s "$ROOT/data/current.png" || return 1
    if /bin/sh /mnt/us/calendar-display/service.sh status | grep -q 'running pid='; then
        touch "$STATE/overlay-running"
    fi
    /etc/init.d/calendar-display stop
    # This marker belongs only to this appliance's private data directory.
    [ ! -e "$ROOT/data/DISABLED" ] || rm "$ROOT/data/DISABLED"
    for target in dev proc sys; do
        mount --bind /"$target" "$ROOT/$target" || return 1
        touch "$STATE/bound-$target"
    done
    chroot "$ROOT" /usr/sbin/eips -f -g /data/current.png || return 1
    for service in framework browserd webreaderd; do
        touch "$STATE/stopped-$service"
        if [ "$service" = framework ]; then
            /etc/init.d/framework stop || return 1
        else
            stop_app "$service" || return 1
        fi
    done
    DATA="$ROOT/data" /bin/sh "$BASE/power-state.sh" > "$STATE/power-state.log" 2>&1 < /dev/null &
    echo $! > "$STATE/power-state.pid"
    chroot "$ROOT" /bin/sh /sbin/display-supervisor > "$STATE/supervisor.log" 2>&1 < /dev/null &
    echo $! > "$STATE/supervisor.pid"
    sleep 6
    kill -0 "$(cat "$STATE/supervisor.pid")" || return 1
    kill -0 "$(cat "$STATE/power-state.pid")" || return 1
    grep -q RENDER_OK "$STATE/supervisor.log" || return 1
    if pidof cvm browserd webreader > /dev/null; then
        echo STOCK_APPLICATION_STILL_RUNNING
        return 1
    fi
    touch "$STATE/READY"
    echo APPLIANCE_READY
}

stock() {
    mkdir "$STATE/restoring" 2>/dev/null || return 0
    echo RESTORE_BEGIN
    if [ -f "$BASE/ENABLED" ]; then
        mv "$BASE/ENABLED" "$BASE/DISABLED" || return 1
    fi
    touch "$ROOT/data/DISABLED"
    sleep 12
    for target in sys proc dev; do
        if [ -f "$STATE/bound-$target" ]; then
            umount "$ROOT/$target" || echo "UNMOUNT_FAILED $target"
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
    touch "$STATE/RESTORED"
    echo STOCK_APPLICATIONS_RESTORED
    if [ "$1" != keep-network ]; then
        if network_ready && [ "$mode" = 1 ]; then
            ifconfig usb0 down
            lipc-set-prop -i -- com.lab126.volumd useUsbForNetwork 0
        fi
        echo STORAGE_REQUESTED
    fi
}

case "$1" in
    boot|start-live)
        test -f "$BASE/ENABLED" || exit 0
        mkdir "$STATE" || exit 1
        /bin/sh "$BASE/manage.sh" watchdog > "$STATE/watchdog.log" 2>&1 < /dev/null &
        echo $! > "$STATE/watchdog.pid"
        if [ "$1" = boot ]; then
            network_start || { echo NETWORK_FAILED; stock; exit 1; }
        fi
        application_start || { echo APPLICATION_FAILED; stock; exit 1; }
        if [ "$1" = boot ] && [ -r "$BASE/IMAGE_URL" ]; then
            /bin/sh "$BASE/wifi-client.sh" > "$STATE/wifi-client.log" 2>&1 < /dev/null &
            echo $! > "$STATE/wifi-client.pid"
            echo WIFI_CLIENT_STARTED
        fi
        ;;
    watchdog)
        sleep 600
        if [ ! -f "$STATE/CONFIRMED" ]; then
            stock
        else
            echo BOOT_CONFIRMED
        fi
        ;;
    confirm)
        test -f "$STATE/READY" && test ! -d "$STATE/restoring" || exit 1
        kill -0 "$(cat "$STATE/supervisor.pid")" || exit 1
        kill -0 "$(cat "$STATE/power-state.pid")" || exit 1
        touch "$STATE/CONFIRMED"
        echo CONFIRMED_THIS_BOOT_ONLY
        ;;
    stock) stock ;;
    stock-keep-network) stock keep-network ;;
    status)
        [ ! -f "$BASE/ENABLED" ] || echo ENABLED_FOR_BOOT
        for flag in READY CONFIRMED RESTORED; do
            [ ! -f "$STATE/$flag" ] || echo "$flag"
        done
        ;;
    *) echo 'Usage: manage.sh {boot|start-live|confirm|stock|stock-keep-network|status}'; exit 2 ;;
esac
