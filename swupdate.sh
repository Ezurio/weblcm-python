#!/bin/sh
# Find our running ubiblock
set -- $(cat /proc/cmdline)
for x in "$@"; do
    case "$x" in
        ubi.block=*)
        BLOCK=${x#*,}
        ;;
    esac
done

if [ -z "$BLOCK" ];
then
        /usr/bin/swupdate -e stable,full-a
else
        if [ "$BLOCK" == 1 ];
        then
                /usr/bin/swupdate -e stable,main-b
        else
                /usr/bin/swupdate -e stable,main-a
        fi
fi
