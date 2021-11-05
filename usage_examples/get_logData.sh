LOGTYPE="${LOGTYPE:-"All"}"
PRIORITY="${PRIORITY:-6}"
DAYS="${DAYS:--1}"

source global_settings

echo -e "\n========================="
echo "Get LogData"

${CURL_APP} --location \
    --request GET "${URL}/logData?type=${LOGTYPE}&priority=${PRIORITY}&days=${DAYS}" \
    --header "Content-Type: application/json" \
    -b cookie --insecure \
| ${JQ_APP}

echo -e "\n"

