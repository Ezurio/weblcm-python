##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

echo -e "\n========================="
echo "Bluetooth ble server stop"

${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{
        "command": "bleStopServer"
        }' \
    | ${JQ_APP}