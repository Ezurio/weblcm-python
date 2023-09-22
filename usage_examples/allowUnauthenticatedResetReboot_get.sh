source global_settings

echo -e "\n\n========================="
echo "Get allow unauthenticated reset and reboot"
${CURL_APP} -s --location --request GET ${URL}/allowUnauthenticatedResetReboot \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw ''\
| ${JQ_APP}

echo -e "\n"