#!/bin/sh

exit_on_error() {
	#Redirect to stderr
	echo ${2} 1>&2

	exit ${1}
}

pre_update() {

	#Prepare arguments for swupdate throuth EnviromentFile
	rm -f /tmp/.swupdate.conf
	echo "IMAGESET=-e ${1}" > /tmp/.swupdate.conf
	if [ $# -eq 2 ]; then
		echo "URL=-d '-u ${2}'" >> /tmp/.swupdate.conf
	fi
	systemctl restart swupdate

	#Provide way for customer scripts to inject logic into the update process
	PRECHECK_SCRIPT=/usr/bin/weblcm-python.scripts/swupdate_custom_precheck.sh
	if [ -x ${PRECHECK_SCRIPT} ] ; then
		error_msg=$(${PRECHECK_SCRIPT}) || exit_on_error 1 "${error_msg}"
	fi

	#Wait until swupdate is ready or killed by caller due to timeout
	FILE=/tmp/sockinstctrl
	while [ ! -S ${FILE} ]
	do
		sleep 1
	done

	systemctl -q is-active swupdate || exit_on_error 1 "Failed to start swupdate service"
}

get_update() {

	# For "download" update, we have to check whether swupdate exists first
	if [ "${1}" = "1" ]; then
		systemctl -q is-active swupdate && exit_on_error 5 "Updating..."
	fi

	# Find our running ubiblock
	read -r cmdline < /proc/cmdline
	set -- ${cmdline}
	for x in "$@"; do
		case "$x" in
			ubi.block=*)
			BLOCK=${x#*,}
			;;
		esac
	done

	bootside=`fw_printenv bootside -n`

	if [ -z "${BLOCK}" ] && [ ${bootside} == 'a' ]; then
		exit 0;
	elif [ "${BLOCK}" == 1 ] && [ ${bootside} == 'b' ]; then
		exit 0;
	elif [ "${BLOCK}" == 4 ] && [ ${bootside} == 'a' ]; then
		exit 0;
	fi

	exit_on_error 1 "Bootside is not updated"
}

post_update() {
	systemctl stop swupdate
}

case "${1}" in
	pre-update)
		pre_update ${2}
		#Success
		exit 0
		;;
	do-update)
		pre_update ${2} ${3}
		#Success
		exit 0
		;;
	get-update)
		get_update ${2}
		;;
	post-update)
		post_update
		#Success
		exit 0
		;;
esac
