#!/bin/sh

bootside=${1}

if [ -z "${bootside}" ] || [ "${bootside}" != "a" ] && [ "${bootside}" != "b" ] ; then
	[ `/usr/sbin/fw_printenv bootside -n` == "a" ] && bootside=b || bootside=a
fi

/usr/sbin/fw_setenv bootside "${bootside}"

/usr/sbin/reboot
