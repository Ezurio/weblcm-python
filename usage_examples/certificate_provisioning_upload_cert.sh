source global_settings

echo -e "\n========================="
echo "Upload signed device server certificate"

REQUEST_URL="${URL}/certificateProvisioning"

${CURL_APP} -s --location \
    --request PUT "${REQUEST_URL}" \
     ${AUTH_OPT} \
    --form 'certificate=@"'"${FILE}"'"' \
| ${JQ_APP}

echo -e "\n"