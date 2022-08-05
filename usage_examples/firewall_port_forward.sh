source global_settings

echo -e "\n========================="
echo "Port forward"

if [ -z "$ZONE" ]
then
    echo "Please invoke with zone set e.g. ZONE=external $0"
    exit
fi
if [ -z "$PORT" ]
then
    echo "Please invoke with port set e.g. PORT=22 $0"
    exit
fi
if [ -z "$PROTOCOL" ]
then
    echo "Please invoke with protocol set e.g. PROTOCOL=tcp/udp $0"
    exit
fi
if [ -z "$TOPORT" ]
then
    echo "Please invoke with to port set e.g. TOPORT=22 $0"
    exit
fi
if [ -z "$TOADDR" ]
then
    echo "Please invoke with to addr set e.g. TOADDR=10.10.5.6 $0"
    exit
fi


echo -e "\nforward port ${VSP_TCP_PORT}:\n"

${CURL_APP} --location --request PUT ${URL}/firewall/${ZONE}/addForwardPort \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    --data '{
        "port": "'"${PORT}"'",
        "protocol": "'"${PROTOCOL}"'",
        "toport": "'"${TOPORT}"'",
        "toaddr": "'"${TOADDR}"'"
        }' \
    | ${JQ_APP}

echo -e "\n\ncheck forwarded ports:\n"
${CURL_APP} --location --request GET ${URL}/firewall/${ZONE} \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    | ${JQ_APP}


