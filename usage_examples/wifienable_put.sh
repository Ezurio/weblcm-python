##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings
ENABLE="${ENABLE:-1}"

echo -e "\n\n========================="
echo "wifi enable put"
${CURL_APP} -s --location --request PUT "${URL}/wifiEnable?enable=${ENABLE}" \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw '' \
| ${JQ_APP}

echo -e "\n"