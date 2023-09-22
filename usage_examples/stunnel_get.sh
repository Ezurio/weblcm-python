source global_settings

echo -e "\n========================="
echo "Get stunnel state"

${CURL_APP} -s --location \
    --request GET ${URL}/stunnel \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw '' \
| ${JQ_APP}

echo -e "\n"