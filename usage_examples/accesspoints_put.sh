source global_settings

echo -e "\n========================="
echo "PUT accesspoints"

${CURL_APP} --header "Content-Type: application/json" \
    --request PUT "${URL}/accesspoints" \
    -b cookie \
    --insecure \
    --data-raw ‘’\
| ${JQ_APP}

echo -e "\n"

