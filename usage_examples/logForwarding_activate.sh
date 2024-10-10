##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

echo -e "\n========================="
echo "Activate LogForwarding"

${CURL_APP} -s --location \
    --request PUT ${URL}/logForwarding \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw '{"state":"active"}' \
| ${JQ_APP}

echo -e "\n"