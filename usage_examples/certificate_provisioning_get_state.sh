source global_settings

echo -e "\n========================="
echo "Get current provisioning state"
echo

REQUEST_URL="${URL}/certificateProvisioning"

${CURL_APP} -s --location \
    --request GET "${REQUEST_URL}" \
     ${AUTH_OPT} \
| ${JQ_APP}

echo -e "\n"