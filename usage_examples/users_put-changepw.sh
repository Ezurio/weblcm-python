source global_settings

echo ""
echo "====="
echo "Change password"

${CURL_APP} -s --header "Content-Type: application/json" \
    --request PUT \
    --data '{"username":"'"${WEBLCM_USERNAME}"'","current_password":"'"${ORIGINAL_WEBLCM_PASSWORD}"'","new_password":"'"${WEBLCM_PASSWORD}"'"}' \
    --insecure ${URL}/users \
    -b cookie \
| ${JQ_APP}

echo -e "\n"
