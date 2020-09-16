#!/usr/bin/python
import os, shutil

basepath = os.path.expanduser('~/sqm-in-a-box/')

configfile = '/tmp/config.ini'
if not os.path.exists(configfile):
	if os.path.exists(basepath + 'config.ini'):
		shutil.copy(basepath + 'config.ini', '/tmp/')

logpath = basepath + 'logs/'
if not os.path.isdir(logpath):
	os.makedirs(logpath)

datapath = basepath + 'data/'
if not os.path.isdir(datapath):
	os.makedirs(datapath)
	
sqm_logfile = basepath +'logs/sqm.log'

import configparser, sys
from distutils.util import strtobool

config = configparser.ConfigParser()
config.read(configfile)

debug = config["debug"]
debugmode = config.get('debug', 'debugmode')

import logging

# set up logging to file - see previous section for more details
if debugmode == 'debug':
	logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
					datefmt='%Y-%m-%d %H:%M',
					filename=sqm_logfile)
	# define a Handler which writes INFO messages or higher to the sys.stderr
	console = logging.StreamHandler()
	console.setLevel(logging.DEBUG)
else:
	logging.basicConfig(level=logging.INFO,
					format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
					datefmt='%Y-%m-%d %H:%M',
					filename=sqm_logfile)
	# define a Handler which writes INFO messages or higher to the sys.stderr
	console = logging.StreamHandler()
	console.setLevel(logging.INFO)

# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

logger = logging.getLogger('get_sqm')

import getpass
current_user = getpass.getuser()

import datetime
today = datetime.datetime.today()

logger.debug('today :' + str(today))

try:
	gps = config["sqm"]
	sqm_type = config.get('sqm', 'type')
	sqm_serial = config.get('sqm', 'serial')
	sqm_connection = config.get('sqm', 'connection')
	sqmdatafile = datapath + config.get('sqm', 'sqmdatafile')
	if sqm_connection == 'eth':
		sqm_address = config.get('sqm', 'sqm_address')
		tcp_port = config.getint('sqm', 'tcp_port')
	elif sqm_connection == 'usb':
		usb_port = config.get('sqm', 'usb_port')

	gps = config["gps"]
	tzn = config.get('gps', 'tzn')
	latitude = config.get('gps', 'lat')
	longitude = config.get('gps', 'lon')
	elevation = config.get('gps', 'elv')
	last_gps_read_string = config.get('gps', 'last_gps_read')

	station = config["station"]
	station_name = config.get('station', 'name')
	station_id = config.get('station', 'station_id')
	is_mobile_string = config.get('station', 'is_mobile')
	is_mobile = strtobool(is_mobile_string)
	apikey = config.get('station', 'apikey')

	sqm = config["sqm"]
	instrument_id = config.get('sqm', 'instrument_id')

	suntimes = config["suntimes"]
	next_sunrise_string = config.get('suntimes', 'next_sunrise')
	next_sunset_string = config.get('suntimes', 'next_sunset')
	
except KeyError as e:
	logger.warn("Error reading the configuration section {}".format(e))

logger.debug('last_gps_read_string: ' + last_gps_read_string)
if last_gps_read_string == '':
	last_gps_read_string = '2000-01-01 00:00:00.000000+12:00'
	
header = '# Light Pollution Monitoring Data Format 1.0\
# URL: http://www.darksky.org/measurements\
# Number of header lines: 36\
# This data is released under the following license: ODbL 1.0 http://opendatacommons.org/licenses/odbl/summary/\
# Device type: SQM-LE\
# Instrument ID: DSNZ008_\
# Data supplier: John Doe, Dark Sky NZ, New Zealand\
# Location name: Auckland\
# Position (lat, lon, elev(m)): -36.8, 174.7, 20\
# Local timezone: Pacific/Auckland\
# Time Synchronization:\
# Moving / Stationary position: STATIONARY\
# Moving / Fixed look direction: FIXED\
# Number of channels: 1\
# Filters per channel: HOYA CM-500 (Standard SQM Filter)\
# Measurement direction per channel: 0,0 (Zenith)\
# Field of view (degrees): FWHM ~ 20 degrees\
# Number of fields per line: 6\
# SQM serial number: 3911\
# SQM hardware identity: 0080A3B8E404\
# SQM firmware version: 4-3-57\
# SQM cover offset value: -0.11\
# SQM readout test ix: i,00000004,00000003,00000057,00003911\
# SQM readout test rx: r, 15.63m,0000000054Hz,0000008648c,0000000.019s, 026.1C\
# SQM readout test cx: c,00000019.95m,0000300.000s, 020.9C,00000008.71m, 024.4C\
# Comment: Location Description\
# Comment: \
# Comment: \
# Comment: \
# Comment: \
# UDM version: 1.0.0.157\
# UDM setting: Logged continuously every 1 minute on the minute,Threshold = 0.00 mpsas.\
# blank line\
# UTC Date & Time, Local Date & Time, Temperature, Counts, Frequency, MSAS, MoonPhaseDeg, MoonElevDeg, MoonIllum\
# YYYY-MM-DDTHH:mm:ss.fff;YYYY-MM-DDTHH:mm:ss.fff;Celsius;number;Hz;mag/arcsec^2;Degrees;Degrees;Percent'
	
import datetime
from datetime import datetime, timedelta
import pytz, tzlocal, zlib
import dateutil.parser

logger.debug('last_gps_read_string: ' + str(last_gps_read_string))
logger.debug(type(last_gps_read_string))

last_gps_read = dateutil.parser.parse(last_gps_read_string)
next_sunrise = dateutil.parser.parse(next_sunrise_string)
next_sunset = dateutil.parser.parse(next_sunset_string)

logger.debug('last_gps_read: ' + str(last_gps_read))
logger.debug(type(last_gps_read))

import time
time.sleep(15)

tz = pytz.timezone(tzn)
now = datetime.now(tz)

if sqm_connection =='eth':
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#s.connect(('unihedron.dyndns.org',10001))
	s.connect((sqm_address,tcp_port))
	
	st = 'rx'
	byt=st.encode()
	s.send(byt)

	msg = ''
	while len(msg) < 56:
		chunk = s.recv(56-len(msg))
		if chunk == '':
			print('raise RuntimeError, "socket connection broken"')
		msg = msg + str(chunk)
	s.close
elif sqm_connection =='usb':
	import serial
	
	ser = serial.Serial(
		port=usb_port,\
		baudrate=115200,\
		parity=serial.PARITY_NONE,\
		stopbits=serial.STOPBITS_ONE,\
		bytesize=serial.EIGHTBITS,\
			timeout=1)
	
	logger.debug("connected to: " + ser.portstr)
	
	ser.write("rx\n")
	ser.flush()
	now = datetime.now(tz)
	logger.debug(ser.readline())
	
	msg = ser
	
	ser.close()

sqm_rx = msg
utc_now = now.astimezone(pytz.utc)

logger.debug('now: ' + str(now))
logger.debug(type(now))
	
mpsas = float(sqm_rx[2:8])
frequency = int(sqm_rx[10:20])
counts = int(sqm_rx[23:33])
period = float(sqm_rx[35:46])
temperature = float(sqm_rx[48:54])

# UTC Date & Time, Local Date & Time, Temperature, Counts, Frequency, MSAS, MoonPhaseDeg, MoonElevDeg, MoonIllum
# YYYY-MM-DDTHH:mm:ss.fff;YYYY-MM-DDTHH:mm:ss.fff;Celsius;number;Hz;mag/arcsec^2;Degrees;Degrees;Percent

logger.debug('Data: ' + str(utc_now.isoformat())  + ';' + str(now.isoformat()) + ';' + str(temperature) + ';' + str(counts) + ';' + str(frequency) + ';' + str(mpsas))

# Moon Calulations

moon_phase_deg = 0.0
moon_elev_deg = 0.0
moon_illum = 0.0

import requests, hashlib

checksum = hashlib.md5((instrument_id + latitude + longitude + apikey).encode()).hexdigest()
logger.debug('checksum: ' + checksum)
logger.debug(type(checksum))



params = (
	('action', 'writesqm'),
	('station_id', station_id),
	('instrument_id', instrument_id),
	('time_utc', utc_now.strftime('%Y-%m-%d %H:%M:%S.%f')),
	('time_local', now.strftime('%Y-%m-%d %H:%M:%S.%f')),
	('temperature', temperature),
	('counts', counts),
	('frequency', frequency),
	('mpsas', mpsas),
	('moon_phase_deg', moon_phase_deg),
	('moon_elev_deg', moon_elev_deg ),
	('moon_illum', moon_illum ),
	('latitude', latitude),
	('longitude', longitude),
	('elevation', elevation),
	('apikey', apikey),
	('checksum', checksum),
)

response = requests.post('https://darkskynz.org/sqminabox/api.php', params=params, headers={'User-Agent': 'Unihedron SQM-LE and Raspberry Pi'})

logger.debug(response.content)

datafile = open(sqmdatafile, "a")
datafile.write(str(utc_now.isoformat())  + ';' + str(now.isoformat()) + ';' + str(temperature) + ';' + str(counts) + ';' + str(frequency) + ';' + str(mpsas) + ';' + str(moon_phase_deg) + ';' + str(moon_elev_deg) + ';' + str(moon_illum) + ';' + str(latitude) + ';' + str(longitude) + ';' + str(elevation) + '\n')
datafile.close()
