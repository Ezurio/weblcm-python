#!/bin/sh

exit_on_error() {
	#Redirect to stderr
	echo ${2} 1>&2

	exit ${1}
}

systemctl restart swupdate
systemctl -q is-active swupdate || exit_on_error 1 "Failed to start swupdate service"

#Wait until swupdate is ready or timeout
FILE=/tmp/sockinstctrl
x=0
while [ ${x} -lt 3 ]
do
	[[ -S ${FILE} ]] && break || sleep 1
	x=$(( ${x} + 1 ))
done
[[ ${x} == 3 ]] && exit_on_error 1 "Failed to run swupdate service"


#Success
exit 0
