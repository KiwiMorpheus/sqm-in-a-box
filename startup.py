#!/usr/bin/python
import os, smtplib, shutil
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def getEthName():
	# Get name of the Ethernet interface
	try:
		for root,dirs,files in os.walk('/sys/class/net'):
			for dir in dirs:
				if dir[:2]=='en' or dir[:3]=='eth':
					interface=dir
	except:
		interface="None"
	return interface

def getMAC(interface='eth0'):
	# Return the MAC address of the specified interface
	try:
		str = open('/sys/class/net/%s/address' %interface).read()
	except:
		str = "00:00:00:00:00:00"
	return str[0:17]

class Emailer:
	def sendmail(self, recipient, subject, content):

		#Create Headers
		headers = ["From: " + mailbox_username, "Subject: " + subject, "To: " + recipient,
				  "MIME-Version: 1.0", "Content-Type: text/html"]
		headers = "\r\n".join(headers)

		#Connect to Gmail Server
		session = smtplib.SMTP(smtp_server, smtp_port)
		session.ehlo()
		session.starttls()
		session.ehlo()

		#Login to Gmail
		session.login(mailbox_username, mailbox_password)

		#Send Email & Exit
		session.sendmail(mailbox_username, recipient, headers + "\r\n\r\n" + content)
		session.quit

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

logger = logging.getLogger('startup')

logger.debug('basepath: ' + basepath)
logger.debug('logpath: ' + logpath)

import getpass
current_user = getpass.getuser()

logger.debug('current_user: ' + current_user)

eth=getEthName()
logger.debug('eth: ' + eth)
pi_mac_address=getMAC(eth)
logger.debug('pi_mac_address: ' + pi_mac_address)

host_name = os.uname()[1]
logger.debug('host_name: ' + host_name)

emailContent = 'Get Pi MAC and hostname\r\n'

# Just a small function to write the file
def write_file():
	config.write(open(configfile, 'w'))

logger.debug('os.path.exists(configfile): ' + str(os.path.exists(configfile)))

if not os.path.exists(configfile):
	config.add_section('gps')
	config.set('gps','timezone', 'Pacific/Auckland')
	config.set('gps','elevation', '14')
	config.set('gps','location_description', 'Auckland, New Zealand')
	config.set('gps','longitude', '174.7')
	config.set('gps','latitude', '-36.8')
	config.set('gps','last_gps_read', '')
	config.add_section('debug')
	config.set('debug','debugmode', 'info')
	config.add_section('station')
	config.set('station','configured', 'False')
	config.set('station','is_mobile', 'False')
	config.set('station','mobile_frequency', '5')
	config.set('station','has_gps', 'False')
	config.set('station','has_internet', 'True')
	config.set('station','station_type', 'connected')
	config.set('station','name', host_name)
	config.set('station','station_id', '')
	config.set('station','update_code', 'False')
	config.add_section('sqm')
	config.set('sqm','connection', 'eth')
	config.set('sqm','sqm_address', '')
	config.set('sqm','tcp_port', '10001')
	config.set('sqm','usb_port', 'dev/ttyUSB0')
	config.set('sqm','has_internet', 'True')
	config.set('sqm','serial', '')
	config.set('sqm','instrument_id', '')
	config.set('sqm','sqmdatafile', '')
	config.add_section('mail')
	config.set('mail','recipient', 'CHANGE ME')
	config.set('mail','frequency', 'False')
	config.set('mail','smtp_server', 'CHANGE ME')
	config.set('mail','smtp_port', '587')
	config.set('mail','mailbox_username', 'CHANGE ME')
	config.set('mail','mailbox_password', 'CHANGE ME')
	
	write_file()
	shutil.copy(configfile, basepath + 'config.ini')
	emailContent += 'Create config.ini\r\n'
	
config.read(configfile)

try:
	gps = config["gps"]
	timezone = config.get('gps', 'timezone')
	latitude = config.getfloat('gps', 'latitude')
	longitude = config.getfloat('gps', 'longitude')
	elevation = config.getfloat('gps', 'elevation')
	location_description = config.get('gps', 'location_description')

	station = config["station"]
	station_id = config.get('station', 'station_id')
	has_internet = strtobool(config.get('station', 'has_internet'))
	is_mobile = strtobool(config.get('station', 'is_mobile'))
	mobile_frequency = config.get('station', 'mobile_frequency')
	has_gps = strtobool(config.get('station', 'has_gps'))
	station_name = config.get('station', 'name')
	configured = strtobool(config.get('station', 'configured'))

	sqm = config["sqm"]
	sqm_type = config.get('sqm', 'type')
	connection = config.get('sqm', 'connection')
	sqm_address = config.get('sqm', 'sqm_address')
	tcp_port = config.get('sqm', 'tcp_port')
	usb_port = config.get('sqm', 'usb_port')
	instrument_id = config.get('sqm', 'instrument_id')

	mail = config["mail"]
	smtp_server = config.get('mail', 'smtp_server')
	smtp_port = int(config.get('mail', 'smtp_port'))
	mailbox_username = config.get('mail', 'mailbox_username')
	mailbox_password = config.get('mail', 'mailbox_password')
	frequency = config.get('mail', 'frequency')

	emailContent += 'Read values from config.ini\r\n'
except KeyError as e:
	logger.warn("Error reading the configuration section {}".format(e))
	emailContent += 'Failed to read values from config.ini\r\n'

logger.debug('timezone: ' + timezone)
logger.debug('latitude: ' + str(latitude))
logger.debug('longitude: ' + str(longitude))
logger.debug('elevation: ' + str(elevation))
logger.debug('is_mobile: ' + str(is_mobile))
logger.debug('has_gps: ' + str(has_gps))
logger.debug('configured: ' + str(configured))
logger.debug('station_name: ' + station_name)

if connection == 'tcp':
	import socket, time, signal, sys

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setblocking(False)                               
	if hasattr(socket,'SO_BROADCAST'):
		s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

	s.sendto("000000f6".decode("hex"), ("255.255.255.255", 30718))

	buf=''
	starttime = time.time()
	while True:
		try:
			(buf, addr) = s.recvfrom(30)
			if buf[3].encode("hex")=="f7":
				print "Received from %s: MAC: %s" % (addr, buf[24:30].encode("hex"))
		except:
			#Timeout in seconds. Allow all devices time to respond
			if time.time()-starttime > 3:
				break
			pass

	#s.connect(('unihedron.dyndns.org',10001))
	#s.connect(('cepheid.dyndns.org',10001))
	try:
		s.connect(('remote.vinstar.com',10001))
	except socket.error as e:
		print(e)
	
	st = 'ix'
	byt=st.encode()
	s.send(byt)

	msg = ''
	while len(msg) < 38:
		chunk = s.recv(38-len(msg))
		if chunk == '':
			print('raise RuntimeError, "socket connection broken"')
		msg = msg + str(chunk)

	sqm_ix = msg

	st = 'rx'
	byt=st.encode()
	s.send(byt)

	msg = ''
	while len(msg) < 56:
		chunk = s.recv(56-len(msg))
		if chunk == '':
			print('raise RuntimeError, "socket connection broken"')
		msg = msg + str(chunk)

	sqm_rx = msg

	st = 'cx'
	byt=st.encode()
	s.send(byt)

	msg = ''
	while len(msg) < 55:
		chunk = s.recv(55-len(msg))
		if chunk == '':
			print('raise RuntimeError, "socket connection broken"')
		msg = msg + str(chunk)

	sqm_cx = msg
	
	emailContent += 'Read values from SQM\r\n'
	# SQM readout test ix: i,00000004,00000003,00000057,00003911
	# SQM readout test rx: r, 16.50m,0000000024Hz,0000019434c,0000000.042s, 021.2C
	# SQM readout test cx: c,00000019.95m,0000300.000s, 020.9C,00000008.71m, 024.4C
	
	a,b,c,d,e = sqm_ix.split(',')
	sqm_device_type = b.strip("0")
	sqm_firmware_version = b.strip("0") + '.' + c.strip("0") + '.' + d.strip("0")
	sqm_serial_number = e.strip("0")

elif connection == 'usb':

	import serial
	ser = serial.Serial(
		port='/dev/ttyUSB0',\
		baudrate=115200,\
		parity=serial.PARITY_NONE,\
		stopbits=serial.STOPBITS_ONE,\
		bytesize=serial.EIGHTBITS,\
			timeout=1)

	print("connected to: " + ser.portstr)
	ser.write("rx\n")
	ser.flush()
	print(ser.readline())
	ser.close()

else:
	connection = 'undetected'


if configured == False:
	import datetime
	from datetime import datetime, timedelta
	import pytz
	import tzlocal

	tz = pytz.timezone(timezone)

	now = datetime.now(tz)
	logger.debug('now: ' + str(now))

	from skyfield.nutationlib import iau2000b

	DAYLENGTH_CENTER_HORIZON = 0.0
	DAYLENGTH_TOP_HORIZON = 0.26667
	DAYLENGTH_TOP_HORIZON_APPARENTLY = 0.8333
	DAYLENGTH_CIVIL_TWILIGHT = 6.0
	DAYLENGTH_NAUTICAL_TWILIGHT = 12.0
	DAYLENGTH_ASTRONOMICAL_TWILIGHT = 18.0

	def daylength(ephemeris, topos, degrees):
		"""Build a function of time that returns the daylength.

		The function that this returns will expect a single argument that is a 
		:class:`~skyfield.timelib.Time` and will return ``True`` if the sun is up
		or twilight has started, else ``False``.
		"""
		sun = ephemeris['sun']
		topos_at = (ephemeris['earth'] + topos).at

		def is_sun_up_at(t):
			"""Return `True` if the sun has risen by time `t`."""
			t._nutation_angles = iau2000b(t.tt)
			return topos_at(t).observe(sun).apparent().altaz()[0].degrees > -degrees

		is_sun_up_at.rough_period = 0.5  # twice a day
		return is_sun_up_at

	from skyfield import api
	from skyfield.api import Loader
	load = Loader(basepath + '/skyfield/skyfield-data/')

	ts = load.timescale()
	planets = load('de421.bsp')

	from skyfield import almanac

	loc = api.Topos(latitude, longitude, elevation_m=elevation)

	t0 = ts.utc(datetime.now(tz))
	t1 = ts.utc(tz.normalize(datetime.now(tz) + timedelta(1)))

	#center_time, center_up = almanac.find_discrete(t0, t1, daylength(planets, loc, DAYLENGTH_CENTER_HORIZON))
	#print('Sunrise Sunset center of sun is even with horizon:')
	#print(center_time.utc_iso(), center_up)

	#astro_twil_time, astro_twil_up = almanac.find_discrete(t0, t1, daylength(planets, loc, DAYLENGTH_ASTRONOMICAL_TWILIGHT))
	twil_time, twil_up = almanac.find_discrete(t0, t1, daylength(planets, loc, DAYLENGTH_CENTER_HORIZON))
	#print('Astronomical twilight:')
	#print('Civil twilight:')
	logger.debug('Civil Twilight: ' + str(twil_time.utc_iso()) + ', ' + str(twil_up))
	logger.debug(type(twil_up))

		
	import numpy as np
	result = np.where(twil_up == False)
	logger.debug(result)
	logger.debug('Sunset Index: ' + str(result[0][0]))
	logger.debug('type(result[0][0].item()): ' + str(type(result[0][0].item())))
	logger.debug('result[0][0].item() == 1: ' + str(result[0][0].item() == 1))

	astro_times = twil_time.utc_iso()
	if result[0][0].item() == 1:
		sunset_utc_time = astro_times[1]
		sunrise_utc_time = astro_times[0]
	else:
		sunset_utc_time = astro_times[0]
		sunrise_utc_time = astro_times[1]

	logger.debug('UTC Sunset time in ISO8601 format: ' + sunset_utc_time)
	logger.debug('UTC Sunrise time in ISO8601 format: ' + sunrise_utc_time)

	import dateutil.parser
	sunset_date = dateutil.parser.parse(sunset_utc_time)
	sunrise_date = dateutil.parser.parse(sunrise_utc_time)

	logger.debug('UTC Sunset time in datetime format: ' + str(sunset_date))
	logger.debug('UTC Sunrise time in datetime format: ' + str(sunrise_date))

	sunset_localtime = sunset_date.astimezone(tz)
	sunrise_localtime = sunrise_date.astimezone(tz)

	logger.debug('Local Sunset time: ' + str(sunset_localtime))
	logger.debug('Local Sunrise time: ' + str(sunrise_localtime))
		
	config.set('suntimes', 'next_sunrise', str(sunrise_localtime))
	config.set('suntimes', 'next_sunset', str(sunset_localtime))

	import socket, hashlib

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#s.connect(('unihedron.dyndns.org',10001))
	#s.connect(('cepheid.dyndns.org',10001))
	try:
		s.connect(('remote.vinstar.com',10001))
	except socket.error as e:
		print(e)
	
	st = 'ix'
	byt=st.encode()
	s.send(byt)

	msg = ''
	while len(msg) < 38:
		chunk = s.recv(38-len(msg))
		if chunk == '':
			print('raise RuntimeError, "socket connection broken"')
		msg = msg + str(chunk)

	sqm_ix = msg

	st = 'rx'
	byt=st.encode()
	s.send(byt)

	msg = ''
	while len(msg) < 56:
		chunk = s.recv(56-len(msg))
		if chunk == '':
			print('raise RuntimeError, "socket connection broken"')
		msg = msg + str(chunk)

	sqm_rx = msg

	st = 'cx'
	byt=st.encode()
	s.send(byt)

	msg = ''
	while len(msg) < 55:
		chunk = s.recv(55-len(msg))
		if chunk == '':
			print('raise RuntimeError, "socket connection broken"')
		msg = msg + str(chunk)

	sqm_cx = msg
	
	emailContent += 'Read values from SQM\r\n'
	# SQM readout test ix: i,00000004,00000003,00000057,00003911
	# SQM readout test rx: r, 16.50m,0000000024Hz,0000019434c,0000000.042s, 021.2C
	# SQM readout test cx: c,00000019.95m,0000300.000s, 020.9C,00000008.71m, 024.4C
	
	a,b,c,d,e = sqm_ix.split(',')
	sqm_device_type = b.strip("0")
	sqm_firmware_version = b.strip("0") + '.' + c.strip("0") + '.' + d.strip("0")
	sqm_serial_number = e.strip("0")

	import requests

	params = (
		('action', 'register_station'),
		('sqm_serial_number', sqm_serial_number),
		('pi_mac_address', pi_mac_address),
		('host_name', host_name),
		('instrument_id', instrument_id),
		('device_type', sqm_device_type),
	)

	response = requests.get('http://darkskynz.org/sqminabox/api.php', params=params, headers={'User-Agent': 'Unihedron SQM/LE and Raspberry Pi'})

	logger.debug('response.status_code: ' + str(response.status_code))
	logger.debug('response.content: ' + str(response.content))

	if response.status_code == 200:
		if response.content != False:
			apikey = response.content
			emailContent += 'response.content: ' + response.content + '\r\n'
			emailContent += 'apikey: ' + apikey + '\r\n'
			emailContent += 'Send Station info to MySQL database and get apikey\r\n'

	logger.debug('apikey: ' + str(apikey))
		
	config.set('sqm', 'type', sqm_device_type)
	config.set('sqm', 'serial', sqm_serial_number)
	config.set('station', 'apikey', apikey)
	
	emailContent += 'update Station info to config.ini\r\n'
	
	from crontab import CronTab
	from datetime import datetime, timedelta

	if now < sunset_localtime + timedelta(seconds=300) and now > sunset_localtime - timedelta(seconds=300):
		next_set_cron = sunrise_localtime
	elif now < sunrise_localtime + timedelta(seconds=300) and now > sunrise_localtime - timedelta(seconds=300):
		next_set_cron = sunset_localtime
	else:
		#next_set_cron = sunrise_localtime
		next_set_cron = sunset_localtime

	nowplus5min = datetime.now() + timedelta(minutes = 5)
	my_cron = CronTab(user=current_user)

	#    my_cron.env['MAILTO'] = 'justin@darkskynz.org'
	exists_query_gps = exists_query_sqm = exists_sunrise_cron = exists_sunset_cron = exists_startup_cron = exists_send_data = exists_get_updates = exists_git_pull = False

	for job in my_cron:
		if "Query GPS" in str(job):
			exists_query_gps = True
		if "Query SQM" in str(job):
			exists_query_sqm = True
		if "Sunrise cron" in str(job):
			exists_sunrise_cron = True
		if "Sunset cron" in str(job):
			exists_sunset_cron = True
		if "Startup cron" in str(job):
			exists_startup_cron = True
		if "Send data" in str(job):
			exists_send_data = True
		if "Get updates" in str(job):
			exists_get_updates = True
		if "git pull code updates" in str(job):
			exists_git_pull = True

	if exists_query_gps == True:
		for job in my_cron.find_comment('Query GPS'):
			job.clear()
			if is_mobile == True:
				job.minute.every(mobile_frequency) # every 5th minute
			else:
				job.hour.on(sunset_localtime.hour)
				job.minute.on(sunset_localtime.minute)

			job.enable(has_gps)
			logger.debug('job: ' +str(job))
			logger.debug('Query GPS cron job modified successfully')
	elif exists_query_gps == False:
		get_gps = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/get_gps_coordinates.py', comment="Query GPS")
		get_gps.minute.every(1)
		get_gps.enable(False)
		logger.debug('Query GPS job created successfully')
	
	my_cron.write()
	
	if exists_query_sqm == True:
		for job in my_cron.find_comment('Query SQM'):
			job.clear()
			if has_gps == True:
				if is_mobile == True:
					job.minute.every(mobile_frequency) # every 5th minute
				else:
					job.minute.every(1) # every minute
			job.enable(True)
			logger.debug('job: ' + str(job))
			logger.debug('Query SQM job modified successfully')
	elif exists_query_sqm == False:	
		get_sqm = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/get_sqm_reading.py', comment="Query SQM")
		get_sqm.minute.every(1)
		get_sqm.enable(True)
		logger.debug('Query SQM job created successfully')

	my_cron.write()

	if exists_startup_cron == False:
		startup_cron = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/startup.py', comment="Startup cron")
		startup_cron.every_reboot()
		logger.debug('Startup cron job created successfully')

	my_cron.write()

	if exists_get_updates == True:
		for job in my_cron.find_comment('Get updates'):
			job.clear()
			job.minute.on(0)
			job.enable(has_internet)
			logger.debug('job: ' + str(job))
			logger.debug('Get updates job modified successfully')
	elif exists_get_updates == False:
		get_updates = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/get_updates.py', comment="Get updates")
		get_updates.minute.on(0)
		get_updates.enable(has_internet)
		logger.debug('Get update cron job created successfully')

	my_cron.write()

	if exists_git_pull == True:
		for job in my_cron.find_comment('git pull code updates'):
			job.clear()
			job.hour.on(12)
			job.minute.on(0)
			job.enable(has_internet)
			logger.debug('job: ' + str(job))
			logger.debug('git pull code updates job modified successfully')
	elif exists_git_pull == False:
		update_git_cron = my_cron.new(command='cd /home/' + current_user + '/sqm-in-a-box/ && git pull && https://darkskynz.org/sqminabox/api.php?action=update_processed&apikey=' + apikey, comment="git pull code updates")
		update_git_cron.hour.on(12)
		update_git_cron.minute.on(0)
		update_git_cron.enable(False)
		logger.debug('git pull code updates cron job created successfully')

	my_cron.write()

	if exists_sunrise_cron == True:
		for job in my_cron.find_comment('Sunrise cron'):
			job.hour.on(sunrise_localtime.hour)
			job.minute.on(sunrise_localtime.minute)
			job.enable(True)
			logger.debug('sunrise_localtime.hour: ' + str(sunrise_localtime.hour))
			logger.debug('sunrise_localtime.minute: ' + str(sunrise_localtime.minute))
			logger.debug('job: ' +str(job))
			logger.debug('Sunrise cron job modified successfully')
	elif exists_sunrise_cron == False:
		sunrise_cron = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/sunrise_cron.py', comment="Sunrise cron")
		sunrise_cron.minute.on(30)
		sunrise_cron.hour.on(5)
		sunrise_cron.enable(True)
		logger.debug('Sunrise cron job created successfully')

	my_cron.write()

	if exists_sunset_cron == True:
		for job in my_cron.find_comment('Sunset cron'):
			job.hour.on(sunset_localtime.hour)
			job.minute.on(sunset_localtime.minute)
			job.enable(True)
			logger.debug('sunset_localtime.hour: ' + str(sunset_localtime.hour))
			logger.debug('sunset_localtime.minute: ' + str(sunset_localtime.minute))
			logger.debug('job: ' +str(job))
			logger.debug('Sunset cron job modified successfully')
	elif exists_sunset_cron == False:
		sunset_cron = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/sunset_cron.py', comment="Sunset cron")
		sunset_cron.minute.on(nowplus5min.minute)
		sunset_cron.hour.on(nowplus5min.hour)
		sunset_cron.enable(True)
		logger.debug('Sunset cron job created successfully')
	
	my_cron.write()

	if exists_send_data == True:
		for job in my_cron.find_comment('Send data'):
			job.clear()
			job.enable(has_internet)
			if frequency == 'daily':
				job.minute.on(0)
				job.hour.on(9)
			elif frequency == 'weekly':
				job.minute.on(0)
				job.hour.on(9)
				job.dow.on('MON')
			elif frequency == 'monthly':
				job.minute.on(0)
				job.hour.on(9)
				job.day.on(1)

			job.enable(has_internet)
		logger.debug('Send data cron job modified successfully')
	elif exists_send_data == False:
		send_data_cron = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/send_data.py', comment="Send data")
		send_data_cron.enable(has_internet)
		if frequency == 'daily':
			send_data_cron.minute.on(0)
			send_data_cron.hour.on(9)
		elif frequency == 'weekly':
			send_data_cron.minute.on(0)
			send_data_cron.hour.on(9)
			send_data_cron.dow.on('MON')
		elif frequency == 'monthly':
			send_data_cron.minute.on(0)
			send_data_cron.hour.on(9)
			send_data_cron.day.on(1)

		send_data_cron.enable(has_internet)
		logger.debug('Send data cron job created successfully')
	
	my_cron.write()

	emailContent += 'Create cron entries if they dont exist\r\n'

	config.set('station', 'configured', str(True))

	# Writing our configuration file to 'config.ini'
	with open(configfile, 'wb') as thisconfigfile:
		config.write(thisconfigfile)
		thisconfigfile.close()
		shutil.copy(configfile, basepath + 'config.ini')

	emailContent += 'Set configured = true and Write updated info to config.ini\r\n'

	sender = Emailer()

	sendTo = 'justin@darkskynz.org'
	emailSubject = station_name + ': Setup Configuration from Pi Startup script'
	emailContent += 'Pi hostname: ' + host_name + '\r\n'
	emailContent += 'Pi MAC Address: ' + pi_mac_address + '\r\n'
	emailContent += 'Pi API Identifier' + apikey + '\r\n'
	emailContent += 'SQM Device type: ' + sqm_device_type + '\r\n'
	# emailContent += 'SQM Instrument ID: ' + sqm_instrument_id + '\n'
	emailContent += 'SQM serial number: ' + sqm_serial_number + '\n'
	# emailContent += 'SQM hardware identity: ' + sqm_hardware_identity + '\r\n'
	emailContent += 'SQM firmware version: ' + sqm_firmware_version
	emailBody = MIMEText(emailContent, 'plain')
	
	"""
 	emailattachment = 'hostname, hostmac, hostapi, sqmtype, sqmserial, sqmfirmware\r\n'
	emailattachment += host_name + ', '
	emailattachment += pi_mac_address + ', '
	emailattachment += apikey + ', '
	emailattachment += sqm_device_type + ', '
    emailattachment += sqm_instrument_id + ', '
	emailattachment += sqm_serial_number + ', '
	emailattachment += sqm_hardware_identity + ', '
	emailattachment += sqm_firmware_version

	emailContent += emailattachment
	"""
	#Sends an email to the "sendTo" address with the specified "emailSubject" as the subject and "emailContent" as the email content.
	sender.sendmail(sendTo, emailSubject, emailContent)


