#!/usr/bin/python
import os, zlib, requests

configfile = '/tmp/config.ini'
device_serial = "3911"
device_type = "4"
#apikey = "5cd7d7343fca9f76e6c12f30a9079248"
apikey = "906eec5adaf6a849e6c241e36e30a920"


action = "getstationid"
checksum = hex(zlib.crc32( device_serial + device_type + apikey))[2:]
print(checksum)

params = (
    ('action', 'getstationid'),
    ('device_serial', device_serial),
    ('device_type', device_type),
    ('apikey', apikey),
    ('checksum', checksum),
)

print('http://darkskynz.org/sqminabox/api.php' + str(params))

res = requests.get('http://darkskynz.org/sqminabox/api.php', params=params, headers={'User-Agent': 'Foo bar'})


#url = "https://darkskynz.org/sqminabox/api.php?action=getstationid&device_serial=" + device_serial + "&device_type=" + device_type + "&apikey=" + apikey + "&checksum=" + checksum
#print(url)

#res = requests.get(url, headers={'User-Agent': 'Foo bar'})
print(res.status_code)
print(res.content)
