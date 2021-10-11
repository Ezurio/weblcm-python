source global_settings


echo -e "\n========================="
echo "Get accesspoints"

${CURL_APP} --location \
    --request GET ${URL}/accesspoints \
    -b cookie --insecure \
| ${JQ_APP}

echo -e "\n"

