#TZ="${TZ:-"America/Los_Angeles"}"

source global_settings

echo -e "\n========================="
echo "Set datetime"

${CURL_APP} --location \
    --request PUT "${URL}/datetime" \
    --header 'Content-Type: application/json' \
    --data '{
    "zone": "'"${TZ}"'"
    }' \
    --insecure \
    -b cookie \
    | ${JQ_APP}



