# Converting Endpoint data to Guest Device data
## Descriptions
Create import file from ClearPass Endpoint database to [Guest Debvice Repository].

Describe three methods to convert Endpoint data to import format.
1. Using SQL statement to extract data from Endpoint and create a CSV file for import.
2. Using XML export from Endpoint database.
3. Using ClearPass REST API  

### Common tasks
- Create device roles for devices
- Update [Guest Roles] Role Mapping with new roles
- Update Role Mappings and Enforcement Policies

### SQL method endpoint2guest.sql
Using psql client to access endopoint db on Clearpass.
Set password for appexternal amd connect to tipsdb database.
Modify SQL statement to reflect your device mappings to roles.

### XML Conversion conv_endpoint_to_guest.py
'''
$ python3 conv_endpoint_to_guest.py -h
usage: conv_endpoint_to_guest.py [-h] [--format {xml,json,csv}] [--category CATEGORY] [--xml-format {pretty,raw}] input output role

Convert ClearPass endpoint XML export to ClearPass Guest import format.

positional arguments:
  input                 Input ClearPass endpoint XML file
  output                Output file (Guest XML or JSON)
  role                  Device role to assign to imported devices (e.g., 'Printer', 'Camera')

options:
  -h, --help            show this help message and exit
  --format {xml,json,csv}
                        Output format (default: xml)
  --category CATEGORY   Filter by endpoint category (e.g., Printer, Server, Computer). Can be specified multiple times.
  --xml-format {pretty,raw}
                        XML formatting style (default: pretty). Only applies to XML output.

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

### REST API cp_get_endpoint.py
#### Requirements
pycentral
requests
urllib3

####  Convert data
- Create REST API client in ClearPass
- Install requirements if needed
- Customize config.ini file to reflect your environment and requirements
- Run script
'''
cp_get_endpoint.py -h
usage: cp_get_endpoint.py [-h] [--cp-host CP_HOST] [--cp-port CP_PORT] [--cp-user CP_USER] [--cp-pass CP_PASS] [--filter FILTER] [--output OUTPUT]
                          [client_id] [client_secret] [grant_type] [limit]

Fetch endpoint info from ClearPass using pyclearpass ApiIdentities.get_endpoint().

options:
  -h, --help         show this help message and exit
  --cp-host CP_HOST  ClearPass hostname or IP address
  --cp-port CP_PORT  ClearPass REST API port (default: 443)
  --cp-user CP_USER  ClearPass API user
  --cp-pass CP_PASS  ClearPass API password. If absent, read from CP_PASSWORD env var
  --filter FILTER    json Filter for endpoint lookup
  --output OUTPUT    Write output JSON to file. Defaults to stdout

API Client Credentials:
  client_id          ClearPass API Client ID (default: endpoint_client)
  client_secret      ClearPass API Client Secret
  grant_type         ClearPass API Grant Type (default: client_credentials)
  limit              ClearPass API Limit (default: 1000)
'''


