source global_settings

echo -e "\n========================="
echo "Get LogLevel"

${CURL_APP} --location \
    --request GET ${URL}/logSetting \
    --header "Content-Type: application/json" \
    -b cookie --insecure \
    --data-raw '' \
| ${JQ_APP}

echo -e "\n"

