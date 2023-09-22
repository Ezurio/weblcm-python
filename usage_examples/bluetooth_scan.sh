source global_settings

echo -e "\n========================="
echo "Bluetooth scan"

echo -e "reset controller, clear cache and force fresh scan:\n"
${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{"powered": 0, "discovering": 0, "discoverable": 0}' \
    | ${JQ_APP} --raw-output
echo -e '\n'

echo -e "\nscan:\n"
${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{"powered": 1, "discovering": 1, "discoverable": 1}' \
    | ${JQ_APP}
echo -e '\n'

echo -e "\nconfirm:\n"
${CURL_APP} --location --request GET ${URL}/bluetooth/${BT_CONTROLLER}?filter=powered,discovering,discoverable \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    | ${JQ_APP}
echo -e '\n'

for i in {1..5}; do
    sleep 5
    reset
    echo -e "\nresults:\n"
    ${CURL_APP} --location --request GET ${URL}/bluetooth/${BT_CONTROLLER}?filter=bluetoothDevices \
         ${AUTH_OPT} \
        | ${JQ_APP}
done

echo -e "\n"