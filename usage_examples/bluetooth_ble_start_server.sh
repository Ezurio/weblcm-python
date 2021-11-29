source global_settings

JQ_APP="${JQ_APP:-smart_jq}"
# tcpPort may be in the range 1000 to 49151
BLE_TCP_PORT="${VSP_TCP_PORT:-1001}"

function smart_jq {
    local input=$(cat)
    if [ "${input:0:1}" == "{" ]; then
        echo "${input}" | jq
    else
        echo "${input}"
    fi
}

echo -e "\n========================="
echo "Bluetooth ble server start"

echo -e "\nopen ble server port ${BLE_TCP_PORT}:\n"

${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    --data '{
        "command": "bleStartServer",
        "tcpPort": "'"${BLE_TCP_PORT}"'"
        }' \
    | ${JQ_APP}

echo -e "\n\nlisten on port:\n"
nc ${IPADDR} ${BLE_TCP_PORT}

