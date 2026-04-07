#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2026
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

"""
Convert ClearPass endpoint export XML into ClearPass Guest import XML

Author: Gorazd Kikelj <gorazd.kikelj@selectium.com>
Version: 1.0.0
Date: 2026-04-03
"""

import re
import json
import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import argparse
import os


# Load configuration
def _load_config():
    '''Load configuration from config.json file.'''
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f'Warning: config.json not found at {config_path}. Using defaults.')
        return {
            'role_id_map': {
                "[Contractor]": "1",
                "[Guest]": "2",
                "[Employee]": "3",
                'Access Point': '4',
                'Security Device': '5',
                'Server': '6',
                'Printer': '8',
            }
        }


_config = _load_config()


def _strip_ns(tag):
    return tag.rsplit('}', 1)[-1] if '}' in tag else tag


def _format_mac(raw_mac):
    if not raw_mac:
        return ''
    cleaned = re.sub(r'[^0-9A-Fa-f]', '', raw_mac)
    if len(cleaned) == 12:
        return '-'.join(cleaned[i:i+2] for i in range(0, 12, 2)).upper()
    return raw_mac.strip()


def _matches_category_filter(endpoint_profile, category_filter):
    '''Check if endpoint profile matches category filter.'''
    if not category_filter:
        return True
    if endpoint_profile is None:
        return False
    ep_category = endpoint_profile.get('category', '') or endpoint_profile.get('deviceInsightTag', '') or ''
    return ep_category.lower() in [c.lower() for c in category_filter]


def get_role_id(role):
    '''Map role string to numeric Role ID for ClearPass Guest import.'''
    role_id_map = _config.get('role_id_map', {})
    return role_id_map.get(role, role)


def convert_endpoints_to_guest(input_xml, role, category_filter=None):
    '''Convert endpoint XML to guest data structure.'''
    tree = ET.parse(input_xml)
    root = tree.getroot()

    role_id = get_role_id(role)

    users = []

    endpoints = root.findall('.//{*}Endpoint')
    if not endpoints:
        endpoints = root.findall('.//Endpoint')

    if not endpoints:
        raise ValueError('No endpoint records found. Check your input XML structure and tags.')

    for ep in endpoints:
        raw_mac = ep.get('macAddress') or ep.get('mac') or ep.get('macaddr') or ''
        mac = _format_mac(raw_mac)

        name = ep.get('host') or ep.get('hostname') or ep.get('name') or ep.get('description') or ''

        endpoint_profile = ep.find('.//{*}EndpointProfile')
        if not name and endpoint_profile is not None:
            name = endpoint_profile.get('host') or endpoint_profile.get('hostname') or endpoint_profile.get('name') or ''

        if category_filter and not _matches_category_filter(endpoint_profile, category_filter):
            continue

        mac = mac.strip()
        if not mac:
            print('No MAC address found for an endpoint, skipping...')
            continue

        user = {
            'id': mac.replace(':', '').replace('-', '').lower(),
            'mac_auth': '1',
            'mac': mac,
            'role': role,
            'role_id': role_id,
            'Visitor Name': name if name else mac,
            "visitor_name": name if name else mac,
            'no_password': '1',
            'do_expire': '0',
            'notes': f'Device imported from endpoint: {name} {mac}'
        }
        if name:
            user['Visitor Name'] = name

        users.append(user)

    return users


def write_xml_output(users, output_file, pretty=True):
    '''Write users data to XML file in ClearPass Guest User format.'''
    # Create root element with namespace
    root = ET.Element('TipsContents', {'xmlns': 'http://www.avendasys.com/tipsapiDefs/1.0'})

    # Add header with current timestamp
    current_time = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %Z')
    header = ET.SubElement(root, 'TipsHeader', {
        'exportTime': current_time,
        'version': '6.0'
    })

    # Create GuestUsers container
    guest_users = ET.SubElement(root, 'GuestUsers')

    for user in users:
        # Create GuestUser element with attributes
        guest_user = ET.SubElement(guest_users, 'GuestUser', {
            'name': user['mac'],
            'startTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sponsorName': 'admin',
            'sponsorProfile': '1',
            'enabled': 'true',
            'guestType': 'DEVICE'
        })

        # Add GuestUserTags for each field
        tags = [
            ('mac', user['mac']),
            ('mac_auth', user['mac_auth']),
            ('Role ID', user['role_id']),
            ('no_password', user['no_password']),
            ('do_expire', user['do_expire']),
            ('source', 'endpoint_import'),
            ('no_portal', '1'),
            ('Create Time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('expire_postlogin', '0'),
            ('simultaneous_use', '1'),
            ('sponsor_profile_name', 'Super Administrator'),
            ('expired_notify_status', '1'),
            ('notes', f'Device imported from endpoint: {user.get("Visitor Name")} {user.get("mac")}')
        ]

        if 'Visitor Name' in user and user['Visitor Name']:
            tags.append(('Visitor Name', user['Visitor Name']))

        for tag_name, tag_value in tags:
            ET.SubElement(guest_user, 'GuestUserTags', {
                'tagName': tag_name,
                'tagValue': str(tag_value)
            })

    if pretty:
        # Convert to string and pretty print with minidom
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent='  ')

        # Write to file with UTF-8 encoding
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
    else:
        # Write raw XML without pretty printing
        guest_tree = ET.ElementTree(root)
        guest_tree.write(output_file, encoding='UTF-8', xml_declaration=True)

    print(f'✅ Conversion complete. Output written to: {output_file}')


def write_json_output(users, output_file):
    '''Write users data to JSON file.'''
    with open(output_file, 'w', encoding='UTF-8') as f:
        json.dump({'users': users}, f, indent=2, ensure_ascii=False)

    print(f'✅ Conversion complete. Output written to: {output_file}')


def write_csv_output(users, output_file):
    '''Write users data to CSV file.'''
    if not users:
        print('No user data to write to CSV.')
        return

    # Get all unique keys from all users
    fieldnames = set()
    for user in users:
        fieldnames.update(user.keys())
    fieldnames = sorted(fieldnames)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

    print(f'✅ Conversion complete. Output written to: {output_file}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert ClearPass endpoint XML export to ClearPass Guest import format.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Configuration:
  The script loads role mappings from config.json in the same directory as the script.
  If config.json is missing, default mappings will be used.
  
  Example config.json:
  {
    "role_id_map": {
      "[Contractor]": "1",
      "[Guest]": "2",
      "[Employee]": "3",        
      "Access Point": "4",
      "Security Device": "5",
      "Server": "6",
      "Printer": "8"
    }
  }
  
  To customize role mappings, edit config.json and modify the "role_id_map" dictionary.
  Role mapping need to be consistent with [Guest Roles] Role Mapping Policy in ClearPass. 
  It is  used to convert role names to numeric IDs for ClearPass Guest import. 
  If a role is not found in the mapping, the original role string will be used.

Examples:
  # Convert to pretty XML with Printer role (default)
  python3 conv_endpoint_to_guest.py input.xml output.xml Printer

  # Convert to raw (compact) XML
  python3 conv_endpoint_to_guest.py input.xml output.xml Printer --xml-format raw

  # Convert to JSON
  python3 conv_endpoint_to_guest.py input.xml output.json Printer --format json

  # Convert to CSV
  python3 conv_endpoint_to_guest.py input.xml output.csv Printer --format csv

  # Filter by category with pretty XML
  python3 conv_endpoint_to_guest.py input.xml output.xml Printer --category Printer --xml-format pretty

  # Multiple filters with raw XML output
  python3 conv_endpoint_to_guest.py input.xml output.xml Printer --category Printer --category Server --xml-format raw

Role mapping:
  Access Point  -> 4
  Security Device -> 5
  Server -> 6
  Printer -> 8
  (other roles are used as provided)
        '''
    )
    parser.add_argument('input', help='Input ClearPass endpoint XML file')
    parser.add_argument('output', help='Output file (Guest XML or JSON)')
    parser.add_argument('role', help="Device role to assign to imported devices (e.g., 'Printer', 'Camera')")
    parser.add_argument('--format', choices=['xml', 'json', 'csv'], default='xml', help='Output format (default: xml)')
    parser.add_argument('--category', action='append', help='Filter by endpoint category (e.g., Printer, Server, Computer). Can be specified multiple times.')
    parser.add_argument('--xml-format', choices=['pretty', 'raw'], default='pretty', help='XML formatting style (default: pretty). Only applies to XML output.')

    args = parser.parse_args()

    users = convert_endpoints_to_guest(args.input, args.role, args.category)
    if args.format == 'json':
        write_json_output(users, args.output)
    elif args.format == 'csv':
        write_csv_output(users, args.output)
    else:
        pretty_xml = (args.xml_format == 'pretty')
        write_xml_output(users, args.output, pretty_xml)

