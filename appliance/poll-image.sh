#!/bin/sh
# Fetch a Kindle-ready PNG, then atomically make it the appliance image.
PATH=/usr/bin:/bin
export PATH
set -u
DATA=/var/local/calendar-appliance/rootfs/data
STATE=/tmp/calendar-appliance
URL=${2:-}
case "$URL" in
    http://*|https://*) ;;
    *) echo 'Usage: poll-image.sh {once|loop} URL [interval-seconds]' >&2; exit 2 ;;
esac

poll_once() {
    [ -f "$STATE/READY" ] && [ ! -d "$STATE/restoring" ] || {
        echo APPLIANCE_NOT_READY >&2
        return 1
    }
    part="$DATA/.incoming-$$.png"
    headers="$STATE/image-headers-$$"
    trap 'rm -f "$part" "$headers"' EXIT
    trap 'exit 0' HUP INT TERM
    args=''
    if [ -s "$DATA/image.etag" ]; then
        etag=$(cat "$DATA/image.etag")
        args="If-None-Match: $etag"
    fi
    if [ -n "$args" ]; then
        code=$(curl -fsSL --connect-timeout 10 --max-time 40 --max-filesize 2000000 \
            -H "$args" -D "$headers" -o "$part" -w '%{http_code}' "$URL") || return 1
    else
        code=$(curl -fsSL --connect-timeout 10 --max-time 40 --max-filesize 2000000 \
            -D "$headers" -o "$part" -w '%{http_code}' "$URL") || return 1
    fi
    if [ "$code" = 304 ]; then
        echo NOT_MODIFIED
        return 0
    fi
    [ "$code" = 200 ] && [ -s "$part" ] || { echo "HTTP_$code" >&2; return 1; }
    # PNG signature, IHDR, width=600 (0x258), height=800 (0x320), 8-bit gray.
    prefix=$(hexdump -v -n 26 -e '1/1 "%02x"' "$part") || return 1
    case "$prefix" in
        89504e470d0a1a0a0000000d4948445200000258000003200800*) ;;
        *) echo INVALID_PNG_HEADER >&2; return 1 ;;
    esac
    old=$(md5sum "$DATA/current.png" | awk '{print $1}')
    new=$(md5sum "$part" | awk '{print $1}')
    if [ "$old" != "$new" ]; then
        mv "$part" "$DATA/current.png" || return 1
        sync
        echo "IMAGE_UPDATED md5=$new"
    else
        echo IMAGE_UNCHANGED
    fi
    etag=$(sed -n 's/^[Ee][Tt][Aa][Gg]: *\(.*\)/\1/p' "$headers" | tail -n 1 | tr -d '\r')
    if [ -n "$etag" ]; then
        echo "$etag" > "$DATA/image.etag.tmp-$$"
        mv "$DATA/image.etag.tmp-$$" "$DATA/image.etag"
    fi
}

case "$1" in
    once) poll_once ;;
    loop)
        interval=${3:-900}
        case "$interval" in *[!0-9]*|'') echo INVALID_INTERVAL >&2; exit 2 ;; esac
        [ "$interval" -ge 60 ] || { echo INTERVAL_TOO_SHORT >&2; exit 2; }
        while :; do
            poll_once || echo POLL_FAILED >&2
            sleep "$interval"
        done
        ;;
    *) echo 'Usage: poll-image.sh {once|loop} URL [interval-seconds]' >&2; exit 2 ;;
esac
