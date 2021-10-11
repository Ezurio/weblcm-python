source global_settings

echo -e "\n========================="
echo "Get datetime"

${CURL_APP} --location \
    --request GET "${URL}/datetime" \
    --header "Content-Type: application/json" \
    -b cookie --insecure \
| ${JQ_APP}
echo -e "\n"

