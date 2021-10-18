source global_settings

echo -e "\n========================="
echo "Reboot"

echo -e "\n\n========================="
echo "Reboot"
${CURL_APP} --location --request PUT ${URL}/reboot \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    --data-raw ''\
| ${JQ_APP}


echo -e "\n"
