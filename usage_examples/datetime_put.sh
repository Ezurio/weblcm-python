#TZ="${TZ:-"America/Los_Angeles"}"

source global_settings

echo -e "\n========================="
echo "Set datetime"

${CURL_APP} -s --location \
    --request PUT "${URL}/datetime" \
    --header 'Content-Type: application/json' \
    --data '{
    "zone": "'"${TZ}"'"
    }' \
    --insecure \
    -b cookie -c cookie \
    | ${JQ_APP}



