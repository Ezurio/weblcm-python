source global_settings

echo -e "\n========================="
echo "Get datetime"

${CURL_APP} -s --location \
    --request GET "${URL}/datetime" \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
| ${JQ_APP}
echo -e "\n"

