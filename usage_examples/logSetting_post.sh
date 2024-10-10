##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
SUPP_LEVEL="${SUPP_LEVEL:-"none"}"
DRIVER_LEVEL="${DRIVER_LEVEL:-0}"

source global_settings

echo -e "\n========================="
echo "Set LogLevel"

${CURL_APP} -s --location \
    --request POST ${URL}/logSetting \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{"suppDebugLevel":"'"${SUPP_LEVEL}"'", "driverDebugLevel":"'"${DRIVER_LEVEL}"'"}' \
| ${JQ_APP}

echo -e "\n"