source global_settings

JQ_APP="${JQ_APP:-smart_jq}"

function smart_jq {
    local input=$(cat)
    if [ "${input:0:1}" == "{" ]; then
        echo "${input}" | jq
    else
        echo "${input}"
    fi
}

echo -e "\n========================="
echo "Bluetooth ble disconnect"

if [ -z "$BT_DEVICE" ]
then
    echo "Please invoke with Bluetooth device address set e.g. BT_DEVICE=xx:xx:xx:xx:xx:xx $0"
    exit
fi

echo -e "\nBluetooth disconnect:\n"
${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    --data '{"command": "bleDisconnect"}' \
    | ${JQ_APP}
echo -e '\n'

echo -e "\nread Bluetooth state:\n"
${CURL_APP} --location --request GET ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    | ${JQ_APP} | grep --color --context=99 Connected
echo -e '\n'

