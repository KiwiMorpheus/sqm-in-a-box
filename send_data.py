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

sqm_logfile = basepath +'logs/sqm.log'
	
datapath = basepath + 'data/'
if not os.path.isdir(datapath):
	os.makedirs(datapath)

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

logger = logging.getLogger('set_cron')

try:
    gps = config["gps"]
    tzn = config.get('gps', 'tzn')
    lat = config.getfloat('gps', 'lat')
    lon = config.getfloat('gps', 'lon')
    elv = config.getfloat('gps', 'elv')
    desc = config.get('gps', 'desc')
    station = config["station"]
    mobilestring = config.get('station', 'is_mobile')
    is_mobile = strtobool(mobilestring)
    hasgpsstring = config.get('station', 'has_gps')
    has_gps = strtobool(hasgpsstring)
    station_name = config.get('station', 'name')
    sqm = config["sqm"]
    sqmdatafile = config.get('sqm', 'sqmdatafile')
    instrument_id = config.get('sqm', 'instrument_id')
    mail = config["mail"]
    smtp_server = config.get('mail', 'smtp_server')
    smtp_port = config.getint('mail', 'smtp_port')
    mailbox_username = config.get('mail', 'mailbox_username')
    mailbox_password = config.get('mail', 'mailbox_password')
    recipient = config.get('mail', 'recipient')
    frequency = config.get('mail', 'frequency')
except KeyError as e:
	logger.warn("Error reading the configuration section {}".format(e))

from datetime import datetime, timedelta
from dateutil.relativedelta import *
from zipfile import ZipFile
import glob

str_today = datetime.today().strftime('%Y-%m-%d')
sending_filename = str_today + '-' + instrument_id + '.zip'
zipObj = ZipFile('/tmp/' + sending_filename, 'w')
 
if frequency.lower() == 'daily':
    email_body_period = ['is yesterdays', '']
    #get the last data file and zip it
    zipObj.write(datapath + sqmdatafile, sqmdatafile)
elif frequency.lower() == 'weekly':
	#get the last 7 data files and zip them
    email_body_period = ['are the last weeks', 's']
    sqmdatafiledate = sqmdatafile.split('_')
    date_end = datetime.strptime(sqmdatafiledate[0], '%Y%m%d')
    date_start = date_end - timedelta(days=7)
    
    os.chdir(datapath)
    files=glob.glob('*.dat')
    for filename in files:
        filename_split = filename.split('_')
        filename_date = datetime.strptime(filename_split[0], '%Y%m%d')
        #print(filename_date)
        if date_start <= filename_date <= date_end:
                zipObj.write(datapath + filename, filename)
elif frequency == 'monthly':
    email_body_period = ['are the last months', 's']
    #get the data files for the month and zip them
    sqmdatafiledate = sqmdatafile.split('_')
    temp_date = datetime.strptime(sqmdatafiledate[0], '%Y%m%d')


# close the Zip File
zipObj.close()

# libraries to be imported 
import smtplib, email
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders
from email import header

fromaddr = mailbox_username
toaddr = recipient
# instance of MIMEMultipart 
msg = MIMEMultipart() 
# storing the senders email address 
msg['From'] = fromaddr 
# storing the receivers email address 
msg['To'] = toaddr 
# string some required headers
msg['Date'] = email.header.Header( email.utils.formatdate(localtime=True) )
msg['Message-ID'] = email.header.Header( email.utils.make_msgid() )
# storing the subject 
msg['Subject'] = str_today + " SQM Data from " + instrument_id
# string to store the body of the mail 
body = 'Attached ' + email_body_period[0] + ' SQM data file' + email_body_period[1]
# attach the body with the msg instance 
msg.attach(MIMEText(body, 'plain')) 
# open the file to be sent 
attachment = open('/tmp/' + sending_filename, "rb") 
# instance of MIMEBase and named as p 
p = MIMEBase('application', 'octet-stream') 
# To change the payload into encoded form 
p.set_payload((attachment).read()) 
# encode into base64 
encoders.encode_base64(p) 
p.add_header('Content-Disposition', "attachment; filename= %s" % sending_filename) 
# attach the instance 'p' to instance 'msg' 
msg.attach(p) 
# creates SMTP session 
s = smtplib.SMTP(smtp_server, smtp_port) 
# start TLS for security 
s.starttls() 
# Authentication 
s.login(fromaddr, mailbox_password) 
# Converts the Multipart msg into a string 
text = msg.as_string() 
# sending the mail 
s.sendmail(fromaddr, toaddr.split(','), text) 
# terminating the session 
s.quit() 