source global_settings

echo -e "\n========================="
echo "Get LogLevel"

${CURL_APP} -s --location \
    --request GET ${URL}/logSetting \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data-raw '' \
| ${JQ_APP}

echo -e "\n"

