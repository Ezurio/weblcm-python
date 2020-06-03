#!/bin/sh

method=${1}
zone=${2}
datetime=${3}

zoneinfo="/usr/share/zoneinfo"
userZoneinfo="/data/misc/zoneinfo"
timeOverrideFile="/tmp/time_override"

exit_on_error() {
	echo ${1}
	exit 1
}

set_timezone(){

	if [ -f "${userZoneinfo}/${zone}" ]; then
		ln -sf "${userZoneinfo}/${zone}"  "${userZoneinfo}/localtime" || exit_on_error "Failed to set time zone"
	else
		ln -sf "${zoneinfo}/${zone}"  "${userZoneinfo}/localtime" || exit_on_error "Failed to set time zone"
	fi
}

set_datetime(){
	date -s "${datetime}" || exit_on_error "Failed to set time"
}

case "${method}" in
	manual)
		set_timezone
		set_datetime
		;;

	auto)
		#Add callback here
		set_timezone
		;;
	check)
		#Add callback here
		[ -f "${timeOverrideFile}" ] || exit 1
		;;
esac
