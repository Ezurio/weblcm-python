source global_settings

echo -e "\n========================="
echo "Get config"

${CURL_APP} --location \
    --request GET "${URL}/file?type=config&password=test" \
    --header "Content-Type: application/json" \
    -b cookie --insecure \
    --data-raw '' \
    --output config.zip

echo "config.zip downloaded"
echo -e "\n"

