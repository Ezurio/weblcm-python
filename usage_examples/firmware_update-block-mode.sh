##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
FIRMWARE="${1}"

if [ -z "${FIRMWARE}" ]; then
    echo usage: ${0} update file
    exit
fi

if [ ! -e "${FIRMWARE}" ]; then
    echo \"${FIRMWARE}\": file not found
    exit
fi

# first - create the block files that you will send with split:
split -b128k -d -a 4 --additional-suffix=.swu-block ${FIRMWARE}

source global_settings

echo -e "\n\n========================="
echo "Firmware update"
echo "========================="
${CURL_APP} -s -S \
    --request DELETE ${AUTH_OPT} \
    ${URL}/firmware | ${JQ_APP}

${CURL_APP} -s -S --header "Content-Type: application/json" \
    --request POST   --data \
    '{"image":"main"}'  ${AUTH_OPT} \
    ${URL}/firmware | ${JQ_APP}

for file in x*.swu-block; do
    echo -e 'sending: '${file}
    ${CURL_APP} -s -S --request PUT ${URL}/firmware --header "Content-type: application/octet-stream"  ${AUTH_OPT} --data-binary @${file}
done

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