#!/bin/sh

exit_on_error() {
	#Redirect to stderr
	echo ${2} 1>&2

	exit ${1}
}

pre_update() {

	systemctl restart swupdate
	systemctl -q is-active swupdate || exit_on_error 1 "Failed to start swupdate service"

	#Wait until swupdate is ready or timeout
	FILE=/tmp/sockinstctrl
	x=0
	while [ ${x} -lt 5 ]
	do
		[[ -S ${FILE} ]] && break || sleep 1
		x=$(( ${x} + 1 ))
	done
	[[ ${x} == 5 ]] && exit_on_error 1 "Failed to run swupdate service"
}

get_update() {

	# Find our running ubiblock
	set -- $(cat /proc/cmdline)
	for x in "$@"; do
		case "$x" in
			ubi.block=*)
			BLOCK=${x#*,}
			;;
		esac
	done

	x=0
	while [ ${x} -lt 5 ]
	do
		bootside=`fw_printenv bootside -n`

		if [ -z "$BLOCK" ] && [ ${bootside} == 'a' ]; then
			break;
		elif [ "$BLOCK" == 1 ] && [ ${bootside} == 'b' ]; then
			break;
		elif [ "$BLOCK" == 4 ] && [ ${bootside} == 'a' ]; then
			break;
		fi

		sleep 1
		x=$(( ${x} + 1 ))
	done
	[[ ${x} == 5 ]] && exit_on_error 1 "Bootside is not updated"
}

post_update() {
	systemctl stop swupdate
}

case $1 in
	pre-update)
		pre_update
		#Success
		exit 0
		;;
	get-update)
		get_update
		#Success
		exit 0
		;;
	post-update)
		post_update
		#Success
		exit 0
		;;
esac
