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
echo "Login with original credentials"

${CURL_APP} -v -s --header "Content-Type: application/json" \
    --request POST \
    --data '{"username":"'"${WEBLCM_USERNAME}"'","password":"'"${ORIGINAL_WEBLCM_PASSWORD}"'"}' \
     ${AUTH_OPT} ${URL}/login \
| ${JQ_APP}

echo -e "\n"

echo ""
echo "====="
echo "Change password"

${CURL_APP} -s --header "Content-Type: application/json" \
    --request PUT \
    --data '{"username":"'"${WEBLCM_USERNAME}"'","current_password":"'"${ORIGINAL_WEBLCM_PASSWORD}"'","new_password":"'"${WEBLCM_PASSWORD}"'"}' \
    ${AUTH_OPT} ${URL}/users \
| ${JQ_APP}

echo -e "\n"