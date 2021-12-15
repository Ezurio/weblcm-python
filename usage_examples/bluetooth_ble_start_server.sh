source global_settings

# tcpPort may be in the range 1000 to 49151
BLE_TCP_PORT="${BLE_TCP_PORT:-1001}"

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

