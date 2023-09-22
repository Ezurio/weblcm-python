UUID="${UUID:-"no-UUID-provided"}"

source global_settings

echo "========================="
echo "DELETE Connection ${UUID}"
${CURL_APP}  \
    -s --request DELETE ${URL}/connection?uuid=${UUID} \
     ${AUTH_OPT} \
| ${JQ_APP}

echo -e "\n"