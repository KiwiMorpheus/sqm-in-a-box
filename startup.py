#!/usr/bin/python
import os, smtplib, shutil
from email.mime.text import MIMEText

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

		from email.mime.text import MIMEText
		from email.mime.multipart import MIMEMultipart

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

import logging
# set up logging to file - see previous section for more details
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

import configparser, sys
from distutils.util import strtobool

eth=getEthName()
logger.debug('eth: ' + eth)
pi_mac_address=getMAC(eth)
logger.debug('pi_mac_address: ' + pi_mac_address)

host_name = os.uname()[1]
logger.debug('host_name: ' + host_name)

emailContent = 'Get Pi MAC and hostname\r\n'

config = configparser.ConfigParser()

# Just a small function to write the file
def write_file():
	config.write(open(configfile, 'w'))

logger.debug('os.path.exists(configfile): ' + str(os.path.exists(configfile)))

if not os.path.exists(configfile):
	config['gps'] = { 'tzn': 'Pacific/Auckland', 'elv': '14', 'desc': 'Auckland, New Zealand', 'lon': '174.7', 'lat': '-36.8', 'last_gps_read': ''}
	config['debug'] = {'debugmode': 'False'}
	config['station'] = {'configured': 'False', 'is_mobile': 'False', 'has_gps': 'False', 'name': host_name, 'station_id': ''}
	config['sqm'] = {'connection': 'eth', 'sqm_address': '', 'tcp_port': '10001', 'usb_port': 'dev/ttyUSB0', 'type': '', 'serial': '', 'instrument_id': '', 'sqmdatafile': ''}
	config['mail'] = {'recipient': 'john@example.com', 'frequency': 'weekly', 'smtp_server': 'mail.domain.com', 'smtp_port': '587', 'mailbox_username': 'CHANGE_ME', 'mailbox_password': 'CHANGE_ME'}
	write_file()
	shutil.copy(configfile, basepath + 'config.ini')
	emailContent += 'Create config.ini\r\n'
	
config.read(configfile)

try:
	gps = config["gps"]
	tzn = config.get('gps', 'tzn')
	lat = config.getfloat('gps', 'lat')
	lon = config.getfloat('gps', 'lon')
	elv = config.getfloat('gps', 'elv')
	desc = config.get('gps', 'desc')

	station = config["station"]
	station_id = config.get('station', 'station_id')
	mobilestring = config.get('station', 'is_mobile')
	is_mobile = strtobool(mobilestring)
	hasgpsstring = config.get('station', 'has_gps')
	has_gps = strtobool(hasgpsstring)
	station_name = config.get('station', 'name')
	configured = config.get('station', 'configured')
	is_configured = strtobool(configured)

	sqm = config["sqm"]
	sqm_type = config.get('sqm', 'type')
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

logger.debug('tzn: ' + tzn)
logger.debug('lat: ' + str(lat))
logger.debug('lon: ' + str(lon))
logger.debug('elv: ' + str(elv))
logger.debug('is_mobile: ' + str(is_mobile))
logger.debug('has_gps: ' + str(has_gps))
logger.debug('configured: ' + str(is_configured))
logger.debug('station_name: ' + station_name)

if is_configured == False:

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

	logger.debug(response.content)

	if response.status_code == 200:
		if response.content != False:
			apikey = response.content
			emailContent += 'Send Station info to MySQL database and get apikey\r\n'

	logger.debug(apikey)
		
	config.set('sqm', 'type', sqm_device_type)
	config.set('sqm', 'serial', sqm_serial_number)
	config.set('station', 'apikey', apikey)
	
	emailContent += 'update Station info to config.ini\r\n'
	from crontab import CronTab
	from datetime import datetime, timedelta

	nowplus5min = datetime.now() + timedelta(minutes = 5)
	my_cron = CronTab(user=current_user)

	#    my_cron.env['MAILTO'] = 'justin@darkskynz.org'

	logger.debug('False' if my_cron.find_comment('Query GPS') else 'True')

	cronjobs = my_cron.find_comment('Query GPS')
	job_exists = False

	for job in cronjobs:
		logger.debug('str(job): ' + str(job))
		if "Query GPS" in str(job):
			job_exists = True
			logger.debug('Query GPS job exists')
			break

	if not job_exists:
		get_gps = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/get_gps_coordinates.py', comment="Query GPS")
		get_gps.minute.every(1)
		get_gps.enable(has_gps)
		my_cron.write()
		logger.debug('Query GPS job created successfully')

	cronjobs = my_cron.find_comment('Query SQM')
	job_exists = False

	for job in cronjobs:
		logger.debug('str(job): ' + str(job))
		if "Query SQM" in str(job):
			job_exists = True
			logger.debug('Query SQM job exists')
			break

	if not job_exists:
		get_sqm = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/get_sqm_reading.py', comment="Query SQM")
		get_sqm.minute.every(1)
		get_sqm.enable(False)
		logger.debug('Query SQM job created successfully')

	cronjobs = my_cron.find_comment('Sunrise cron')
	job_exists = False

	for job in cronjobs:
		logger.debug('str(job): ' + str(job))
		if "Sunrise cron" in str(job):
			job_exists = True
			logger.debug('Sunrise cron job exists')
			break

	if not job_exists:
		sunrise_cron = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/sunrise_cron.py', comment="Sunrise cron")
		sunrise_cron.minute.on(30)
		sunrise_cron.hour.on(5)
		sunrise_cron.enable(True)
		logger.debug('Sunrise cron job created successfully')

	cronjobs = my_cron.find_comment('Sunset cron')
	job_exists = False

	for job in cronjobs:
		logger.debug('str(job): ' + str(job))
		if "Sunset cron" in str(job):
			job_exists = True
			logger.debug('Sunset cron job exists')
			break

	if not job_exists:
		sunset_cron = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/sunset_cron.py', comment="Sunset cron")
		sunset_cron.minute.on(nowplus5min.minute)
		sunset_cron.hour.on(nowplus5min.hour)
		sunset_cron.enable(True)
		logger.debug('Sunset cron job created successfully')

	cronjobs = my_cron.find_comment('Startup cron')
	job_exists = False

	for job in cronjobs:
		logger.debug('str(job): ' + str(job))
		if "Startup cron" in str(job):
			job_exists = True
			logger.debug('Startup cron job exists')
			break

	if not job_exists:
		startup_cron = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/startup.py', comment="Startup cron")
		startup_cron.every_reboot()
		logger.debug('Startup cron job created successfully')

	cronjobs = my_cron.find_comment('Send data')
	job_exists = False

	for job in cronjobs:
		logger.debug('str(job): ' + str(job))
		if "Send data" in str(job):
			job_exists = True
			logger.debug('Send data cron job exists')
			break

	if not job_exists:
		send_data_cron = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/send_data.py', comment="Send data")
		send_data_cron.enable(True)
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
		else:
			send_data_cron.enable(False)
		logger.debug('Send data cron job created successfully')

	my_cron.write()

	emailContent += 'Create cron entries if they dont exist\r\n'

	#config.set('station', 'configured', "True")
	write_file()
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
	emailBody = MIMEText(emailContent)
	
	"""
 	emailAttachment = 'hostname, hostmac, hostapi, sqmtype, sqmserial, sqmfirmware\r\n'
	emailAttachment += host_name + ', '
	emailAttachment += pi_mac_address + ', '
	emailAttachment += apikey + ', '
	emailAttachment += sqm_device_type + ', '
    emailAttachment += sqm_instrument_id + ', '
	emailAttachment += sqm_serial_number + ', '
	emailAttachment += sqm_hardware_identity + ', '
	emailAttachment += sqm_firmware_version

	emailContent += emailAttachment
	"""
	#Sends an email to the "sendTo" address with the specified "emailSubject" as the subject and "emailContent" as the email content.
	sender.sendmail(sendTo, emailSubject, emailContent)
