#FILE=user2.pem
#TYPE=cert

source global_settings

echo ""
echo "========================="
echo "Delete cert file for Network Manager"

${CURL_APP} -s --request DELETE "${URL}/file?file=${FILE}&type=${TYPE}" \
     ${AUTH_OPT} \
    | ${JQ_APP}

echo -e "\n"