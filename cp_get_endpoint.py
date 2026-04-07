#!/usr/bin/env python3
"""Fetch endpoint details from ClearPass via pyclearpass ApiIdentities.get_endpoint()."""

# MIT License
#
# Copyright (c) 2025 Aruba, a Hewlett Packard Enterprise company
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__author__ = "Gorazd Kikelj"
__version__ = "1.0.8"

import argparse
import configparser
import json
import os
import re
import sys
from pyclearpass import * 


def parse_args():
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    parser = argparse.ArgumentParser(
        description="Fetch endpoint info from ClearPass using pyclearpass ApiIdentities.get_endpoint()."
    )

    parser.add_argument("--cp-host", default=config.get('DEFAULT', 'cp-host', fallback=None), required=False, help="ClearPass hostname or IP address")
    parser.add_argument("--cp-port", default=config.getint('DEFAULT', 'cp-port', fallback=443), type=int, help="ClearPass REST API port (default: 443)")
    parser.add_argument("--cp-user", default=config.get('DEFAULT', 'cp-user', fallback=None), required=False, help="ClearPass API user")
    parser.add_argument("--cp-pass", default=config.get('DEFAULT', 'cp-pass', fallback=None), required=False, help="ClearPass API password. If absent, read from CP_PASSWORD env var")
    parser.add_argument("--filter", default=config.get('DEFAULT', 'filter', fallback={}), help="json Filter for endpoint lookup")

    group = parser.add_argument_group(title="API Client Credentials")
    group.add_argument('client_id', default=config.get('API_CLIENT', 'client_id', fallback="endpoint_client"), nargs='?', help="ClearPass API Client ID (default: endpoint_client)")
    group.add_argument('client_secret', default=config.get('API_CLIENT', 'client_secret', fallback=None), nargs='?', help="ClearPass API Client Secret")
    group.add_argument('grant_type', default=config.get('API_CLIENT', 'grant_type', fallback="client_credentials"), nargs='?', help="ClearPass API Grant Type (default: client_credentials)")
    group.add_argument('limit', default=config.get('API_CLIENT', 'limit', fallback=1000), type=int, nargs='?', help="ClearPass API Limit (default: 1000)")
    parser.add_argument("--output", default=config.get('DEFAULT', 'output', fallback=None), help="Write output JSON to file. Defaults to stdout")


    return parser.parse_args()


def main():
    args = parse_args()
    API_Client_ID = args.client_id
    API_Client_Secret = args.client_secret
    API_ClearPass_Host = f'https://{args.cp_host}:443/api'
    API_Grant_Type=args.grant_type
    API_Username = args.cp_user
    API_Password = args.cp_pass or os.environ.get("CP_PASSWORD")  
    print(f"🔐 Authenticating to ClearPass at {API_ClearPass_Host} with client ID '{API_Client_ID}'...'{API_Client_Secret}' ")
    cp = ClearPassAPILogin(
        server=API_ClearPass_Host,
        granttype=API_Grant_Type,
        clientid=API_Client_ID,
        clientsecret=API_Client_Secret,
        username=API_Username,
        password=API_Password,
        verify_ssl=False,
    )
    filter   = json.loads(args.filter.strip("'").rstrip("'")) if args.filter else {}
    try:
        result = ApiIdentities.get_endpoint(cp,limit=1000,offset=0,filter=json.dumps(filter),profile_details=True)
    except TypeError:
        # fallback, if signature is get_endpoint(endpoint_id=None, mac_address=None)
        pass

    if result is None:
        print("No endpoint data found.", file=sys.stderr)
        sys.exit(3)

    payload = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"✅ Endpoint details written to {args.output}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
