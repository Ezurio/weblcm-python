##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

echo -e "\n========================="
echo "Fips GET"

${CURL_APP} -s --location --request GET ${URL}/fips \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw ''\
    | ${JQ_APP}

echo -e "\n========================="
echo "Fips PUT"

echo -e "empty:\n"
${CURL_APP} -s --location --request PUT ${URL}/fips \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{}'\
    | ${JQ_APP}
echo -e '\n'

echo -e "invalid:\n"
${CURL_APP} -s --location --request PUT ${URL}/fips \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{"fips":"status"}'\
    | ${JQ_APP}
echo -e '\n'

echo -e "fips:\n"
${CURL_APP} -s --location --request PUT ${URL}/fips \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{"fips":"fips"}'\
    | ${JQ_APP}

echo -e "unset:\n"
${CURL_APP} -s --location --request PUT ${URL}/fips \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{"fips":"unset"}'\
    | ${JQ_APP}

echo -e "\nChange in FIPS state not active until system reboot"