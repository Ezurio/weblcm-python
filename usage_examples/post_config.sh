source global_settings

echo -e "\n========================="
echo "POST config"

${CURL_APP} --location \
    --request POST "${URL}/file" \
    --insecure \
    -b cookie \
    --form 'type="config"' \
    --form 'file=@"config.zip"' \
    --form 'password="test"'

echo -e "\nconfig.zip uploaded. Reboot to take effect"


