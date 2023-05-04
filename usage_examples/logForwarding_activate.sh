source global_settings

echo -e "\n========================="
echo "Activate LogForwarding"

${CURL_APP} -s --location \
    --request PUT ${URL}/logForwarding \
    --header "Content-Type: application/json" \
    -b cookie --insecure \
    --data-raw '{"state":"active"}' \
| ${JQ_APP}

echo -e "\n"

