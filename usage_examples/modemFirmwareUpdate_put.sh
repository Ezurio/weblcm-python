source global_settings

echo -e "\n\n========================="
echo "Modem Firmware Put"
${CURL_APP} -s --location --request PUT ${URL}/modemFirmwareUpdate \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw ''\
| ${JQ_APP}

echo -e "\n"