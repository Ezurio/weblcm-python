source global_settings

echo -e "\n========================="
echo "Get LogForwarding"

${CURL_APP} -s --location \
    --request GET ${URL}/logForwarding \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw '' \
| ${JQ_APP}

echo -e "\n"