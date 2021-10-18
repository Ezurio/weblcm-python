UUID="${UUID:-"a760e87e-e23a-4ea6-81f9-c4e29052db27"}"
source global_settings


echo -e "\n========================="
echo "Get connection"

${CURL_APP} --location \
    --request GET "${URL}/connection?uuid=${UUID}" \
    -b cookie --insecure \
| ${JQ_APP}

echo -e "\n"

