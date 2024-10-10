##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source global_settings

echo -e "\n========================="
echo "Remove NTP sources"

${CURL_APP} -s --location \
    --request PUT ${URL}/ntp/removeSource \
    --header "Content-Type: application/json" \
     ${AUTH_OPT} \
    --data '{
        "sources": [
            "time.nist.gov"
        ]
    }'\
| ${JQ_APP}
echo -e "\n"