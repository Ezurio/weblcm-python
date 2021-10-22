source global_settings

echo "========================="
echo "definitions"
${CURL_APP} --header "Content-Type: application/json" \
    --request GET \
    ${URL}/definitions \
    -b cookie --insecure \
| ${JQ_APP}
echo -e "\n"
