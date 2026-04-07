
COPY (
SELECT 
  upper(substring(mac_address, 1,2) || '-' || 
        substring(mac_address, 3,2) || '-' || 
        substring(mac_address, 5,2) || '-' || 
        substring(mac_address, 7,2) || '-' || 
        substring(mac_address, 9,2) || '-' || 
        substring(mac_address, 11,2)) as mac,
  CASE WHEN (hostname IS NOT NULL AND hostname != '') THEN hostname ELSE mac_address END AS visitor_name,
  CASE 
    WHEN lower(device_category) = 'monitoring devices' THEN '4'
    WHEN lower(device_category) = 'camera' THEN '5'
    WHEN lower(device_category) = 'printer' THEN '6'
    ELSE '2' 
  END AS role_id,
  1 as mac_auth,
  0 as do_expire,
  'Device imported from Endpoint: '  || mac_address || ' (' || hostname || ')' as notes
  FROM public.tips_endpoints_view 
  WHERE device_category LIKE 'Printer'
    AND mac_address ~ '^[A-Fa-f0-9:\-]*$'
) TO stdout
WITH CSV HEADER;
