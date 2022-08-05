source global_settings

echo -e "\n========================="
echo "List forwarded ports"


if [ -z "$ZONE" ]
then
    zone_add=""
else
    zone_add="/${ZONE}"
fi


echo -e "\n\ncheck forwarded ports:\n"
${CURL_APP} --location --request GET ${URL}/firewall${zone_add} \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    | ${JQ_APP}


