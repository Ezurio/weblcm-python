source global_settings

echo -e "\n\n========================="
echo "Suspend"
${CURL_APP} -s --location --request PUT ${URL}/suspend \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw ''\
| ${JQ_APP}

echo -e "\n"