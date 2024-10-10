##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

echo -e "\n========================="
echo "Deactivate LogForwarding"

${CURL_APP} -s --location \
    --request PUT ${URL}/logForwarding \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw '{"state":"inactive"}' \
| ${JQ_APP}

echo -e "\n"