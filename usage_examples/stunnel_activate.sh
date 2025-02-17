##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

echo -e "\n========================="
echo "Activate stunnel"

${CURL_APP} -s --location \
    --request PUT ${URL}/stunnel \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw '{"state":"active"}' \
| ${JQ_APP}

echo -e "\n"