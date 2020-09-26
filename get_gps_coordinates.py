#!/usr/bin/python
import os, shutil

basepath = os.path.expanduser('~/sqm-in-a-box/')

configfile = os.path.expanduser('/tmp/config.ini')
if not os.path.exists(configfile):
	if os.path.exists(basepath + 'config.ini'):
		shutil.copy(basepath + 'config.ini', '/tmp/')

logpath = basepath + 'logs/'
if not os.path.isdir(logpath):
	os.makedirs(logpath)

logpath = basepath + 'data/'
if not os.path.isdir(logpath):
	os.makedirs(logpath)
	
sqm_logfile = basepath +'logs/sqm.log'

import configparser, sys
from distutils.util import strtobool

config = configparser.ConfigParser()
config.read(configfile)

try:
    debug = config["debug"]
    debugmode = config.get('debug', 'debugmode')
except:
    debugmode = 'debug'

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

logger = logging.getLogger('get_gps')

logger.debug('sqm_logfile: ' + str(sqm_logfile))
import getpass
current_user = getpass.getuser()

try:
    gps = config["gps"]
    timezone = config.get('gps', 'timezone')
    last_elevation = config.getint('gps', 'elevation')
    last_location_description = config.get('gps', 'location_description')
    last_longitude = config.getfloat('gps', 'longitude')
    last_latitude = config.getfloat('gps', 'latitude')
    last_gps_read_string = config.get('gps', 'last_gps_read')
    has_gps = strtobool(config.get('gps', 'has_gps'))
    station = config["station"]
    is_mobile = strtobool(config.get('station', 'is_mobile'))
    mobile_frequency = int(config.get('station', 'mobile_frequency'))
    suntimes = config["suntimes"]
    next_sunrise_string = config.get('suntimes', 'next_sunrise')
    next_sunset_string = config.get('suntimes', 'next_sunset')
except KeyError as e:
    logger.warn("Error reading the configuration section {}".format(e))

from crontab import CronTab
my_cron = CronTab(user=current_user)

import datetime
today = datetime.datetime.today()

logger.info('Today: ' + str(today))

import datetime
from datetime import datetime, timedelta
import pytimezone
import timezonelocal
import dateutil.parser

logger.info('last_gps_read_string: ' + str(last_gps_read_string))
logger.info(type(last_gps_read_string))

last_gps_read = dateutil.parser.parse(last_gps_read_string)
next_sunrise = dateutil.parser.parse(next_sunrise_string)
next_sunset = dateutil.parser.parse(next_sunset_string)

logger.info('last_gps_read: ' + str(last_gps_read))
logger.info(type(last_gps_read))

timezone = pytimezone.timezone(timezone)

now = datetime.now(timezone)
logger.info('now: ' + str(now))
logger.info(type(now))

diff_gps_reads = now - last_gps_read
logger.info('diff_gps_reads: ' + str(diff_gps_reads))
logger.info('diff_gps_reads.total_seconds(): ' + str(diff_gps_reads.total_seconds()))
    
#Get GPS data from GPS device
#TODO - GPS interface code
# Placeholder data
curr_desc = 'Auckland'
curr_elv = 20
curr_lon = 174.8
curr_lat = -36.9

from geopy.distance import distance

d = distance((last_latitude, last_longitude, last_elevation), (curr_lat, curr_lon, curr_elv)).m
logger.debug(str(d))

gps_error_margin = 5
next_gps_read = now

if d > gps_error_margin:
    logger.info('Station has moved ' + str(d) + ' meters since ' + str(last_gps_read))
    config.set('gps', 'elevation', str(curr_elv))
    config.set('gps', 'longitude', str(curr_lon))
    config.set('gps', 'latitude', str(curr_lat))
    config.set('gps', 'location_description', str(curr_desc))
    config.set('gps', 'last_gps_read', str(now))
    next_gps_read = now + timedelta(seconds=300)
elif d <= gps_error_margin:
    logger.info('GPS difference reading of ' + str(d) + ' meters within margin of error since ' + str(last_gps_read))
    config.set('gps', 'last_gps_read', str(now))
    if now < next_sunset + timedelta(seconds=300) and now > next_sunset - timedelta(seconds=300):
        next_gps_read = next_sunrise
    elif now < next_sunrise + timedelta(seconds=300) and now > next_sunrise - timedelta(seconds=300):
        next_gps_read = next_sunset

# Writing our configuration file to 'config.ini'
with open(configfile, 'wb') as thisconfigfile:
    config.write(thisconfigfile)
    thisconfigfile.close()

exists_query_gps = False

for job in my_cron:
    if "Query GPS" in str(job):
        exists_query_gps = True

if exists_query_gps == True:
    for job in my_cron.find_comment('Query GPS'):
        job.clear()
        if is_mobile == True:
            job.minute.every(mobile_frequency) # every 5th minute
        else:
            job.hour.on(next_gps_read.hour)
            job.minute.on(next_gps_read.minute)

        job.enable(has_gps)
        logger.debug('job: ' +str(job))
        logger.debug('Query GPS cron job modified successfully')
elif exists_query_gps == False:
    get_gps = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/get_gps_coordinates.py', comment="Query GPS")
    get_gps.hour.on(next_gps_read.hour)
    get_gps.minute.on(next_gps_read.minute)
    get_gps.enable(has_gps)
    logger.debug('Query GPS job created successfully')
	
my_cron.write()
