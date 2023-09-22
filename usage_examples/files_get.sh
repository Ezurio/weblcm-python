TYPE="${TYPE:-"pac"}"

source global_settings

echo -e "\n========================="
echo "Get list of ${TYPE} files (supports 'pac' and 'cert')"

${CURL_APP} -s --location \
    --request GET "${URL}/files?type=${TYPE}" \
     ${AUTH_OPT} \
    --data-raw ''\
| ${JQ_APP}
echo -e "\n"