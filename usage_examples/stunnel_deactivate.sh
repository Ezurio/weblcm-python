source global_settings

echo -e "\n========================="
echo "Deactivate stunnel"

${CURL_APP} -s --location \
    --request PUT ${URL}/stunnel \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw '{"state":"inactive"}' \
| ${JQ_APP}

echo -e "\n"