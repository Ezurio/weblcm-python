source global_settings

echo -e "\n========================="
echo "Get config"

${CURL_APP} --location \
    --request GET "${URL}/file?type=log" \
    --header "Content-Type: application/json" \
    -b cookie --insecure \
    --data-raw ''

echo -e "\n"

