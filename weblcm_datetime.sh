#!/bin/sh

method=${1}
zone=${2}
datetime=${3}

ZONE_INFO="/usr/share/zoneinfo"
LOCALTIME="/etc/localtime"
TIMEZONE="/etc/timezone"

exit_on_error() {
    echo ${1}
    exit 1
}

set_timezone(){
    ln -nsf "${ZONE_INFO}"/"${zone}"  $(touch /etc >& /dev/null && echo "${LOCALTIME}" || readlink "${LOCALTIME}") || error_on_exit 'Failed to create "${LOCALTIME}" link'

    echo "${zone}" > "${TIMEZONE}" || exit_on_error "Failed to set time zone"
}

set_datetime(){
    date -s "${datetime}" > /dev/null || exit_on_error "Failed to set time"
}

if [ "${zone}" ]; then
	set_timezone
else

    case "${method}" in
        manual)
            set_datetime
            ;;

        auto)
            #Add callback here
            ;;
        check)
            #Return date and time
            date '+%Y-%m-%d %H:%M:%S'
            ;;
    esac
fi
