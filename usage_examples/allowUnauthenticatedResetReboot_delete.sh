source global_settings

echo -e "\n\n========================="
echo "delete (reset) allow unauthenticated reset and reboot"
${CURL_APP} -s --location --request DELETE ${URL}/allowUnauthenticatedResetReboot \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw ''\
| ${JQ_APP}


echo -e "\n"
