##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

echo -e "\n\n========================="
echo "set allow unauthenticated reset and reboot"

${CURL_APP} -s --location --request PUT ${URL}/allowUnauthenticatedResetReboot \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data-raw ''\
| ${JQ_APP}

echo -e "\n"