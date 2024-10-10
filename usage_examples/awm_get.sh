##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

echo -e "\n========================="
echo "AWM Get"

${CURL_APP} -s --location --request GET ${URL}/awm \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw ''\
    | ${JQ_APP}

echo -e "\n"