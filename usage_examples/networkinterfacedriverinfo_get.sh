IFNAME="${IFNAME:-"wlan0"}"
source global_settings

echo "========================="
echo "network interface driver info"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request GET \
    ${URL}/networkInterfaceDriverInfo?name=${IFNAME} \
     ${AUTH_OPT} \
| ${JQ_APP}
echo -e "\n"