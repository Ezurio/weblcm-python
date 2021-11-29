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
echo "Bluetooth ble start discovery"

${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    --data '{
        "command": "bleStartDiscovery"
        }' \
    | ${JQ_APP}

