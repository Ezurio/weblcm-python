FIRMWARE=http://192.168.1.123:8080/som60.swu

source global_settings


echo -e "\n\n========================="
echo "Firmware update"
echo "========================="
${CURL_APP} -s --header "Content-Type: application/json" \
    --request POST   --data \
    '{"image":"full", "url":"'"${FIRMWARE}"'"}'  --insecure \
    ${URL}/firmware -b cookie

echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=1 -b cookie
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=1 -b cookie
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=1 -b cookie
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=1 -b cookie
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=1 -b cookie
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=1 -b cookie
echo && sleep 5
${CURL_APP} -s --request GET --insecure ${URL}/firmware?mode=1 -b cookie
echo "You will need to reboot the device once the update is complete"


${CURL_APP} -s --request DELETE --insecure ${URL}/firmware -b cookie


echo ""
echo "Done"

