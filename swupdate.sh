#!/bin/sh
if  [ "$(/usr/sbin/fw_printenv -n bootside)" == b ]; then
	/usr/bin/swupdate -e stable,main-a
else
	/usr/bin/swupdate -e stable,main-b
fi
