source global_settings

echo -e "\n========================="
echo "Wifi enable Get"

${CURL_APP} -s --location --request GET ${URL}/wifiEnable \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw ''\
    | ${JQ_APP}

echo -e "\n"