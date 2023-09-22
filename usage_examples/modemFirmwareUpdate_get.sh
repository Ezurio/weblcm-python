source global_settings

echo -e "\n========================="
echo "Modem Firmware Update Get"

${CURL_APP} -s --location --request GET ${URL}/modemFirmwareUpdate \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw ''\
    | ${JQ_APP}

echo -e "\n"