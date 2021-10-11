UUID="${UUID:-"no-UUID-provided"}"

source global_settings

echo "========================="
echo "DELETE Connection ${UUID}"
${CURL_APP}  \
    --request DELETE ${URL}/connection?uuid=${UUID} \
    -b cookie --insecure \
| ${JQ_APP}

echo -e "\n"



