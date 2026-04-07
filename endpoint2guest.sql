
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
    WHEN lower(device_category) = 'monitoring devices' THEN 'iot'
    WHEN lower(device_category) = 'camera' THEN 'security'
    ELSE device_category 
  END AS role_id,
  1 as mac_auth,
  0 as do_expire
  FROM public.tips_endpoints_view 
  WHERE device_category LIKE 'Printer'
) TO stdout
WITH CSV HEADER;
