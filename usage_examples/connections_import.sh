source global_settings
ARCHIVE_PASSWORD="${ARCHIVE_PASSWORD:-"1234"}"

echo "========================="
echo "Import connections"
${CURL_APP} -s --location \
    --request PUT \
    "${URL}/files?type=network&password=${ARCHIVE_PASSWORD}" \
     ${AUTH_OPT} \
    --form 'archive=@"connections.zip"' \
| ${JQ_APP}

echo -e "\n"