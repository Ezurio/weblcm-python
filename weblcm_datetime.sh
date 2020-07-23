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
	/usr/sbin/hwclock --systohc -l
}

set_datetime(){
	date -s "${datetime}" > /dev/null || exit_on_error "Failed to set time"
	/usr/sbin/hwclock --systohc -l
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
			[ -f "${timeOverrideFile}" ] || exit 1
			;;
	esac
fi
