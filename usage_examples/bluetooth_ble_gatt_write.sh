##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

# Example UUIDs taken from Nordic nRF Connect SDK peripheral uart example project
GATT_SVC_UUID="${GATT_SVC_UUID:-6e400001-b5a3-f393-e0a9-e50e24dcca9e}"
GATT_CHR_UUID="${GATT_CHR_UUID:-6e400002-b5a3-f393-e0a9-e50e24dcca9e}"

echo -e "\n========================="
echo "Bluetooth GATT write"
echo "Please invoke bluetooth_ble_connect.sh prior to receive response."

if [ -z "${BT_DEVICE}" ]
then
    echo "Please invoke with Bluetooth device address set e.g. BT_DEVICE=xx:xx:xx:xx:xx:xx $0"
    exit
fi

if [ -z "${GATT_DATA}" ]
then
    echo "Please enter data to send IN HEXADECIMAL encoding, and press ENTER"
    read GATT_DATA
    echo "sending '${GATT_DATA}'..."
fi

${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{
        "command": "bleGatt",
        "operation": "write",
        "value": "'"${GATT_DATA}"'",
        "svcUuid": "'"${GATT_SVC_UUID}"'",
        "chrUuid": "'"${GATT_CHR_UUID}"'"
        }' \
    | ${JQ_APP}