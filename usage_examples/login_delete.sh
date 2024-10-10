##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

# Logout
echo ""
echo "======"
echo "logout"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request DELETE \
    ${AUTH_OPT} ${URL}/login \
| ${JQ_APP}

echo -e "\n"