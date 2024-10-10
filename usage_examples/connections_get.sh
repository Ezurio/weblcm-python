##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

echo "========================="
echo "Connections"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request GET \
    ${URL}/connections \
     ${AUTH_OPT} \
| ${JQ_APP}

echo -e "\n"