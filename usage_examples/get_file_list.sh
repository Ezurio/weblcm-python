TYPE="${TYPE:-"pac"}"

source global_settings

echo -e "\n========================="
echo "Get list of ${TYPE} files"

${CURL_APP} --location \
    --request GET "${URL}/files?type=${TYPE}" \
    -b cookie --insecure \
    --data-raw ''\

echo -e "\n"

