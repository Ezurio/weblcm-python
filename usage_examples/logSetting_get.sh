source global_settings

echo -e "\n========================="
echo "Get LogLevel"

${CURL_APP} -s --location \
    --request GET ${URL}/logSetting \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw '' \
| ${JQ_APP}

echo -e "\n"