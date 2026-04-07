#!/usr/bin/env python3
"""Fetch endpoint details from ClearPass via pyclearpass ApiIdentities.get_endpoint()."""

import argparse
import json
import os
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch endpoint info from ClearPass using pyclearpass ApiIdentities.get_endpoint()."
    )

    parser.add_argument("--cp-host", required=True, help="ClearPass hostname or IP address")
    parser.add_argument("--cp-port", default=443, type=int, help="ClearPass REST API port (default: 443)")
    parser.add_argument("--cp-user", required=True, help="ClearPass API user")
    parser.add_argument("--cp-pass", required=False, help="ClearPass API password. If absent, read from CP_PASSWORD env var")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--endpoint-id", type=int, help="ClearPass endpoint ID")
    group.add_argument("--mac", help="MAC address of endpoint to look up")

    parser.add_argument("--output", help="Write output JSON to file. Defaults to stdout")

    return parser.parse_args()


def main():
    args = parse_args()
    cp_password = args.cp_pass or os.environ.get("CP_PASSWORD")
    if not cp_password:
        print("Error: password not provided via --cp-pass or CP_PASSWORD", file=sys.stderr)
        sys.exit(1)

    try:
        from pyclearpass import Clearpass
    except ImportError:
        print("Error: pyclearpass is not installed. Install with 'pip install pyclearpass'", file=sys.stderr)
        sys.exit(2)

    cp = Clearpass(
        host=args.cp_host,
        username=args.cp_user,
        password=cp_password,
        port=args.cp_port,
        verify_ssl=False,
    )

    try:
        # ApiIdentities.get_endpoint usually accepts endpoint ID; some versions may accept mac_address.
        if args.endpoint_id is not None:
            result = cp.ApiIdentities.get_endpoint(args.endpoint_id)
        else:
            result = cp.ApiIdentities.get_endpoint(mac_address=args.mac)
    except TypeError:
        # fallback, if signature is get_endpoint(endpoint_id=None, mac_address=None)
        result = cp.ApiIdentities.get_endpoint(endpoint_id=args.endpoint_id, mac_address=args.mac)

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
