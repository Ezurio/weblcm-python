source global_settings

echo -e "\n========================="
echo "Fips Get"

${CURL_APP} --location --request GET ${URL}/fips \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    --data-raw ''\
    | ${JQ_APP}

echo -e "\n"
