#FILE=user2.pem

source global_settings

echo ""
echo "========================="
echo "Upload cert file for Network Manager"
${CURL_APP} --request POST \
    ${URL}/file \
    -b cookie --insecure \
    --form 'type="cert"' \
    --form 'file=@"'"${FILE}"'"'

echo -e "\n"


