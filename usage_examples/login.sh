source global_settings

echo ""
echo "====="
echo "Login"

${CURL_APP} --header "Content-Type: application/json" \
    --request POST \
    --data '{"username":"'"${WEBLCM_USERNAME}"'","password":"'"${WEBLCM_PASSWORD}"'"}' \
    --insecure ${URL}/login \
    -c cookie \
| ${JQ_APP}


echo -e "\n"
