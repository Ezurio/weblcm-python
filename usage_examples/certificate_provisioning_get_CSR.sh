source global_settings

COUNTRY_NAME="${COUNTRY_NAME:-"US"}"
STATE_OR_PROVINCE_NAME="${STATE_OR_PROVINCE_NAME:-"OH"}"
LOCALITY_NAME="${LOCALITY_NAME:-"Akron"}"
ORGANIZATION_NAME="${ORGANIZATION_NAME:-"LairdConnectivity"}"
ORGANIZATIONAL_UNIT_NAME="${ORGANIZATIONAL_UNIT_NAME:-"IT"}"
COMMON_NAME="${COMMON_NAME:-"Summit"}"

echo -e "\n========================="
echo "Get device server CSR using the specified subject info"
echo
echo "Country Name: ${COUNTRY_NAME}"
echo "State/Province Name: ${STATE_OR_PROVINCE_NAME}"
echo "Locality Name: ${LOCALITY_NAME}"
echo "Organization Name: ${ORGANIZATION_NAME}"
echo "Organizational Unit Name: ${ORGANIZATIONAL_UNIT_NAME}"
echo "Common Name: ${COMMON_NAME}"

REQUEST_URL="${URL}/certificateProvisioning"

${CURL_APP} -s --location \
    --request POST "${REQUEST_URL}" \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "countryName": "'"${COUNTRY_NAME}"'",
        "stateOrProvinceName": "'"${STATE_OR_PROVINCE_NAME}"'",
        "localityName": "'"${LOCALITY_NAME}"'",
        "organizationName": "'"${ORGANIZATION_NAME}"'",
        "organizationalUnitName": "'"${ORGANIZATIONAL_UNIT_NAME}"'",
        "commonName": "'"${COMMON_NAME}"'"
    }' \
    --output dev.csr

echo -e "\n"

