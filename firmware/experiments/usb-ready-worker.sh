#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
trap '' HUP
BASE=/var/local/calendar-usb-boot-test-4

ready() {
    mode=$(lipc-get-prop com.lab126.volumd useUsbForNetwork 2>/dev/null) || return 1
    case "$mode" in 0|1) return 0 ;; *) return 1 ;; esac
}

recover() {
    mkdir "$BASE/recovering" 2>/dev/null || return 0
    echo RECOVERY_BEGIN
    if [ -f "$BASE/sshd.pid" ]; then
        pid=$(cat "$BASE/sshd.pid")
        case "$pid" in
            ''|*[!0-9]*) ;;
            *)
                if [ "$(readlink /proc/$pid/exe)" = /mnt/us/usbnet/bin/dropbearmulti ]; then
                    kill -TERM "$pid"
                fi
                ;;
        esac
    fi
    if ready; then
        if [ "$mode" = 1 ]; then
            ifconfig usb0 down
            lipc-set-prop -i -- com.lab126.volumd useUsbForNetwork 0 || return 1
        fi
        echo RECOVERY_STORAGE_REQUESTED
    else
        echo RECOVERY_NO_VOLUMD
    fi
    touch "$BASE/FINISHED"
}

case "$1" in
    check)
        ready || exit 1
        echo "VOLUMD_READY mode=$mode"
        test -x /usr/bin/dropbear || exit 1
        test -r /mnt/us/usbnet/etc/authorized_keys || exit 1
        echo SSH_ASSETS_PRESENT
        ;;
    fallback)
        sleep 600
        if [ -f "$BASE/ACK" ]; then
            echo USB_BOOT_ACKNOWLEDGED
        else
            recover
        fi
        ;;
    start)
        echo USB_BOOT_TEST_STARTED
        /bin/sh "$BASE/worker.sh" fallback > "$BASE/fallback.log" 2>&1 < /dev/null &
        echo $! > "$BASE/fallback.pid"
        count=0
        until ready; do
            count=$((count + 1))
            if [ "$count" -ge 90 ]; then
                echo VOLUMD_READINESS_TIMEOUT
                exit 1
            fi
            sleep 1
        done
        echo "VOLUMD_READY seconds=$count mode=$mode"
        lipc-set-prop -i -- com.lab126.volumd useUsbForNetwork 1 || exit 1
        count=0
        until [ -d /sys/class/net/usb0 ] && [ -x /usr/bin/dropbear ] && [ -r /mnt/us/usbnet/etc/authorized_keys ]; do
            count=$((count + 1))
            if [ "$count" -ge 45 ]; then
                echo NETWORK_ASSET_TIMEOUT
                ifconfig usb0
                lipc-get-prop com.lab126.volumd useUsbForNetwork
                ls -l /usr/bin/dropbear /mnt/us/usbnet/etc/authorized_keys
                dmesg | grep -i -e g_ether -e g_file_storage -e gadget -e 'resource busy'
                grep -i -e volumd -e g_ether -e 'resource busy' /var/log/messages | tail -n 60
                exit 1
            fi
            sleep 1
        done
        ifconfig usb0 192.168.15.244 netmask 255.255.255.0 up || exit 1
        /usr/bin/dropbear -s -p 192.168.15.244:22 -P "$BASE/sshd.pid" -K 15 || exit 1
        sleep 1
        kill -0 "$(cat "$BASE/sshd.pid")" || exit 1
        ifconfig usb0
        echo USB_BOOT_TEST_READY
        ;;
    *) exit 2 ;;
esac
