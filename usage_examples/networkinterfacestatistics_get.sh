##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
IFNAME="${IFNAME:-"wlan0"}"
source global_settings

echo "========================="
echo "network interface statistics"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request GET \
    ${URL}/networkInterfaceStatistics?name=${IFNAME} \
     ${AUTH_OPT} \
| ${JQ_APP}
echo -e "\n"