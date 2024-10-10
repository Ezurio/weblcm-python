##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

if [ -f cookie ]; then
    rm cookie
fi

echo ""
echo "====="
echo "Login"

${CURL_APP} -v -s --header "Content-Type: application/json" \
    --request POST \
    --data '{"username":"'"${WEBLCM_USERNAME}"'","password":"'"${WEBLCM_PASSWORD}"'"}' \
    ${AUTH_OPT} ${URL}/login \
| ${JQ_APP}

echo -e "\n"
