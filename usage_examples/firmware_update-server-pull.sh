##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
FIRMWARE="${1}"

if [ -z "${FIRMWARE}" ]; then
    echo usage: ${0} firmware url, e.g. http://192.168.1.123:8080/som60.swu
    exit
fi

. ./global_settings

echo -e "\n\n========================="
echo "Firmware update"
echo "========================="
echo "Requesting device pull FW from ${FIRMWARE}..."
echo
${CURL_APP} -s --header "Content-Type: application/json" \
    --request POST   --data \
    '{"image":"full", "url":"'"${FIRMWARE}"'"}' ${AUTH_OPT} \
    ${URL}/firmware

SUCCESS=false
echo
echo
while true; do
    echo "Checking status:"
    ${CURL_APP} -s --request GET ${AUTH_OPT} ${URL}/firmware | tee status | ${JQ_APP}
    echo
    if grep -q Updated status; then
        SUCCESS=true
        break
    fi
    if grep -q Failed status; then
        break
    fi
    sleep 1
done

echo
${SUCCESS} && . ./reboot_put.sh

echo ""
echo "Done"
