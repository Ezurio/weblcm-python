source global_settings

echo -e "\n========================="
echo "Factory Reset"

${CURL_APP} -s --location --request PUT ${URL}/factoryReset \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw ''\
| ${JQ_APP}

echo -e "\n\n========================="
echo "Reboot required"
echo -e "\n"
