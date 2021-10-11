source global_settings

echo -e "\n========================="
echo "AWM Get"

${CURL_APP} --location --request GET ${URL}/awm \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    --data-raw ''\
    | ${JQ_APP}

echo -e "\n"
