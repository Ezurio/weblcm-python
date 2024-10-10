##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
UUID="${UUID:-"a760e87e-e23a-4ea6-81f9-c4e29052db27"}"
source global_settings


echo -e "\n========================="
echo "Get connection"

${CURL_APP} -s --location \
    --request GET "${URL}/connection" \
     ${AUTH_OPT} \
| ${JQ_APP}

echo -e "\n"