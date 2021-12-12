# first - create the block files that you will send with split:

# split -b128k -d -a 4 --additional-suffix=.swu-block som60.swu

echo run the split command in this file and then remove the following exit
# then remove this exit
exit

source global_settings


echo -e "\n\n========================="
echo "Firmware update"
echo "========================="
${CURL_APP} -s -S --header "Content-Type: application/json" \
    --request POST   --data \
    '{"image":"main"}'  --insecure \
    ${URL}/firmware -b cookie | ${JQ_APP}

for file in x*.swu-block; do
    echo -e 'sending: '${file}
    ${CURL_APP} -s -S --request PUT ${URL}/firmware --header "Content-type: application/octet-stream" -b cookie --insecure --data-binary @${file}
done

${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=0 -b cookie | ${JQ_APP}
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=0 -b cookie | ${JQ_APP}
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=0 -b cookie | ${JQ_APP}
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=0 -b cookie | ${JQ_APP}
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=0 -b cookie | ${JQ_APP}
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=0 -b cookie | ${JQ_APP}
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=0 -b cookie | ${JQ_APP}
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=0 -b cookie | ${JQ_APP}

${CURL_APP} -s --request DELETE --insecure ${URL}/firmware -b cookie | ${JQ_APP}
echo "You will need to reboot the device once the update is complete"


