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

import logging
# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.DEBUG,
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

from crontab import CronTab
my_cron = CronTab(user=current_user)

import datetime
today = datetime.datetime.today()

logger.info('Today: ' + str(today))

import configparser, sys
from distutils.util import strtobool

config = configparser.ConfigParser()
config.read(configfile)
debugmode = False

try:
    gps = config["gps"]
    tzn = config.get('gps', 'tzn')
    last_elv = config.getint('gps', 'elv')
    last_desc = config.get('gps', 'desc')
    last_lon = config.getfloat('gps', 'lon')
    last_lat = config.getfloat('gps', 'lat')
    last_gps_read_string = config.get('gps', 'last_gps_read')
    station = config["station"]
    is_mobile_string = config.get('station', 'is_mobile')
    is_mobile = strtobool(is_mobile_string)
    next_sunrise_string = config.get('suntimes', 'next_sunrise')
    next_sunset_string = config.get('suntimes', 'next_sunset')
except KeyError as e:
    logger.warn("Error reading the configuration section {}".format(e))

import datetime
from datetime import datetime, timedelta
import pytz
import tzlocal
import dateutil.parser

logger.info('last_gps_read_string: ' + str(last_gps_read_string))
logger.info(type(last_gps_read_string))

last_gps_read = dateutil.parser.parse(last_gps_read_string)
next_sunrise = dateutil.parser.parse(next_sunrise_string)
next_sunset = dateutil.parser.parse(next_sunset_string)

logger.info('last_gps_read: ' + str(last_gps_read))
logger.info(type(last_gps_read))

tz = pytz.timezone(tzn)

now = datetime.now(tz)
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

d = distance((last_lat, last_lon, last_elv), (curr_lat, curr_lon, curr_elv)).m
if debugmode == True:
    print(d)

gps_error_margin = 5
next_gps_read = now
gps_cron_enable = False

if d > gps_error_margin:
    logger.info('Station has moved ' + str(d) + ' meters since ' + str(last_gps_read))
    config.set('gps', 'elv', str(curr_elv))
    config.set('gps', 'lon', str(curr_lon))
    config.set('gps', 'lat', str(curr_lat))
    config.set('gps', 'desc', str(curr_desc))
    config.set('gps', 'last_gps_read', str(now))
    next_gps_read = now + timedelta(seconds=300)
    gps_cron_enable = True
elif d <= gps_error_margin:
    logger.info('GPS difference reading of ' + str(d) + ' meters within margin of error since ' + str(last_gps_read))
    config.set('gps', 'last_gps_read', str(now))
    if now < next_sunset + timedelta(seconds=300) and now > next_sunset - timedelta(seconds=300):
        next_gps_read = next_sunrise
    elif now < next_sunrise + timedelta(seconds=300) and now > next_sunrise - timedelta(seconds=300):
        next_gps_read = next_sunset
    gps_cron_enable = True

# Writing our configuration file to 'config.ini'
with open(configfile, 'wb') as thisconfigfile:
    config.write(thisconfigfile)
    thisconfigfile.close()
jobexists = False

for job in my_cron:
    if job.comment == 'Query GPS':
        if next_gps_read > now:
            job.hour.on(next_gps_read.hour)
            job.minute.on(next_gps_read.minute)
        jobexists = True
        job.enable(gps_cron_enable)
        logger.info('job: ' +str(job))
        my_cron.write()
    	print 'Cron job modified successfully'

if jobexists == False:
    job = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/get_gps_coordinates.py', comment="Query GPS")
    job.hour.on(next_gps_read.hour)
    job.minute.on(next_gps_read.minute)
    job.enable(False)
    my_cron.write()

