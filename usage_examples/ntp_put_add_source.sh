source global_settings

echo -e "\n========================="
echo "Add NTP sources"

${CURL_APP} -s --location \
    --request PUT ${URL}/ntp/addSource \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{
        "sources": [
            "time.nist.gov"
        ]
    }'\
| ${JQ_APP}
echo -e "\n"