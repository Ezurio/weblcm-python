source global_settings

echo -e "\n========================="
echo "Versions"

${CURL_APP} --header "Content-Type: application/json" \
    --location \
    --request GET ${URL}/version \
    -b cookie --insecure \
| ${JQ_APP}

echo -e "\n"

